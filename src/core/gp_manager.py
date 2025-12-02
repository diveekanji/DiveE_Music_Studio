# src/core/gp_manager.py

import zipfile
import xml.etree.ElementTree as ET
import shutil
import os
import re
from pathlib import Path

class GPManager:
    """
    .gp (Guitar Pro 7/8) ファイルを操作するクラス。
    XMLを解析し、トラック名のリネームや楽器情報の抽出を行う。
    名前空間の有無、タグの大文字小文字揺れ、楽器タイプ記述などあらゆる手段で楽器を特定する。
    """
    
    # MIDI Program Number Mapping
    MIDI_INSTRUMENT_MAP = {
        # Guitars
        25: "Acoustic Guitar", 26: "E.Guitar (Jazz)", 27: "E.Guitar (Clean)",
        28: "E.Guitar (Muted)", 29: "E.Guitar (Overdrive)", 30: "E.Guitar (Dist)",
        # Basses
        32: "Acoustic Bass", 33: "E.Bass (Finger)", 34: "E.Bass (Pick)",
        35: "E.Bass (Fretless)", 36: "Slap Bass 1", 37: "Slap Bass 2",
        38: "Synth Bass 1", 39: "Synth Bass 2",
        # Others
        0: "Piano", 118: "Synth Drum", 119: "Reverse Cymbal"
    }

    def __init__(self, gp_file_path):
        self.file_path = Path(gp_file_path)
        self.work_dir = self.file_path.parent / "gp_processing_temp"
        self.xml_path = self.work_dir / "Content" / "score.gpif"

    def _extract(self):
        if self.work_dir.exists():
            try: shutil.rmtree(self.work_dir)
            except: pass
        with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
            zip_ref.extractall(self.work_dir)

    def _pack(self, output_path):
        output_path = Path(output_path)
        if output_path.exists():
            try: os.remove(output_path)
            except: pass
            
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in self.work_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(self.work_dir)
                    zf.write(file, arcname)
        
        try: shutil.rmtree(self.work_dir)
        except: pass

    def analyze_and_rename_tracks(self, output_path=None):
        self._extract()
        
        if not self.xml_path.exists():
            raise FileNotFoundError("Invalid .gp file: score.gpif not found.")

        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        
        # 名前空間検知
        ns_map = {}
        use_ns = False
        m = re.match(r'\{(.*)\}', root.tag)
        if m:
            ns_url = m.group(1)
            ns_map = {'gp': ns_url}
            use_ns = True
            ET.register_namespace('', ns_url)

        def get_path(tag_name):
            return f".//gp:{tag_name}" if use_ns else f".//{tag_name}"

        # トラック検索
        if use_ns:
            tracks = root.findall(get_path('Track'), ns_map)
        else:
            tracks = root.findall(get_path('Track'))
            
        print(f"Tracks found: {len(tracks)}")
        
        track_info_list = []
        
        for index, track in enumerate(tracks):
            midi_program = -1 # 未検出状態
            is_bass_candidate = False
            
            # --- 判定ロジック1: MIDIプログラム番号 ---
            if use_ns:
                sound_elem = track.find(get_path('Sound'), ns_map)
            else:
                sound_elem = track.find(get_path('Sound'))

            if sound_elem is not None:
                # Midiタグを探す (<Midi> または <MIDI>)
                midi_elem = None
                if use_ns:
                    midi_elem = sound_elem.find(get_path('Midi'), ns_map)
                else:
                    midi_elem = sound_elem.find('Midi')
                    if midi_elem is None:
                        midi_elem = sound_elem.find('MIDI') # ★修正: ここで大文字タグをキャッチ
                
                if midi_elem is not None:
                    # Programタグを探す
                    program_elem = None
                    if use_ns:
                        program_elem = midi_elem.find('gp:Program', ns_map)
                    else:
                        program_elem = midi_elem.find('Program')
                    
                    if program_elem is not None:
                        midi_program = int(program_elem.text)
                        
                    # ドラム判定
                    if use_ns:
                        chan_elem = midi_elem.find('gp:PrimaryChannel', ns_map)
                    else:
                        chan_elem = midi_elem.find('PrimaryChannel')
                    
                    if chan_elem is not None and int(chan_elem.text) == 9:
                        midi_program = 118 # Force drum

            # --- 判定ロジック2: 楽器タイプ記述 (InstrumentSet > Type) ---
            # MIDIが0(Piano)または不明の場合のバックアップ
            if midi_program <= 0:
                if use_ns:
                    inst_set = track.find(get_path('InstrumentSet'), ns_map)
                else:
                    inst_set = track.find('InstrumentSet')
                
                if inst_set is not None:
                    if use_ns:
                        type_elem = inst_set.find('gp:Type', ns_map)
                    else:
                        type_elem = inst_set.find('Type')
                    
                    if type_elem is not None and type_elem.text:
                        t_text = type_elem.text.lower()
                        # XML内の "electricGuitar" や "electricBass" を判定
                        if "bass" in t_text:
                            is_bass_candidate = True
                            if midi_program <= 0: midi_program = 33 # Finger Bass (仮)
                        elif "guitar" in t_text:
                            if midi_program <= 0: midi_program = 30 # Dist Guitar (仮)

            # --- 判定ロジック3: 弦の本数 (<Pitches>の数) ---
            # それでも不明なら、チューニング情報を見る
            if not is_bass_candidate and midi_program <= 0:
                # XML全文検索でPitchesを探す（簡易実装）
                try:
                    track_str = ET.tostring(track, encoding='unicode')
                    pitches_match = re.search(r'<Pitches>([\d\s]+)</Pitches>', track_str)
                    if pitches_match:
                        pitches = pitches_match.group(1).strip().split()
                        string_count = len(pitches)
                        # 4弦または5弦で、低い音程(45=A1以下)が含まれていればベースとみなす
                        if string_count in [4, 5]:
                            if any(int(p) < 45 for p in pitches): 
                                is_bass_candidate = True
                                midi_program = 33
                except:
                    pass

            # --- 最終決定 ---
            if midi_program == -1: midi_program = 0 # Default Piano
            
            base_name = self.MIDI_INSTRUMENT_MAP.get(midi_program, f"Inst {midi_program}")
            
            # パーカッション以外で、MIDIがベース範囲外でも、is_bass_candidateなら強制的にベース名にする
            if is_bass_candidate and not (32 <= midi_program <= 39):
                new_name = "E.Bass (Detected)"
                is_bass = True
            else:
                new_name = base_name
                is_bass = (32 <= midi_program <= 39)

            # XML書き換え
            if use_ns:
                name_elem = track.find('gp:Name', ns_map)
            else:
                name_elem = track.find('Name')

            if name_elem is not None:
                original_name = name_elem.text
                name_elem.text = new_name
            else:
                original_name = "(No Name)"
                new_elem = ET.SubElement(track, 'Name')
                new_elem.text = new_name

            track_info = {
                "index": index,
                "original_name": original_name,
                "new_name": new_name,
                "midi_program": midi_program,
                "is_bass": is_bass
            }
            track_info_list.append(track_info)
            print(f"  [{index}] {original_name} -> {new_name} (Bass: {is_bass})")

        # 保存
        tree.write(self.xml_path, encoding='UTF-8', xml_declaration=True)
        
        target_path = output_path if output_path else self.file_path
        self._pack(target_path)
        
        return track_info_list