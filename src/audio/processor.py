# src/audio/processor.py
import os
import numpy as np
import librosa
import soundfile as sf

class AudioPostProcessor:
    # クロマベクトルに対応するコード名の定義
    CHORD_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    @staticmethod
    def create_click_track(bpm, sr, total_duration_sec, beats_per_bar=4):
        """指定されたBPMでクリック音を生成する"""
        beat_duration = 60 / bpm
        beat_samples = int(beat_duration * sr)
        
        t = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
        envelope = np.exp(-t * 30)
        click_wave = 0.5 * np.sin(2 * np.pi * 1000 * t) * envelope
        
        one_beat = np.zeros(beat_samples)
        copy_len = min(len(click_wave), len(one_beat))
        one_beat[:copy_len] = click_wave[:copy_len]
        
        total_beats = int((total_duration_sec / 60) * bpm) + beats_per_bar
        full_click_track = np.tile(one_beat, total_beats)
        
        return full_click_track

    @staticmethod
    def estimate_chords(y, sr):
        """
        簡易的なコード解析を行う。
        全体を一定間隔で区切り、最も支配的なクロマ（音階）を検出してメジャーコードとして返す。
        ※本格的な解析には機械学習が必要ですが、ここでは軽量な信号処理アプローチを採用します。
        """
        # 高調波成分とパーカッション成分を分離（和音成分を強調）
        y_harmonic, _ = librosa.effects.hpss(y)
        
        # クロマグラム（12音階の強度分布）を計算
        chroma = librosa.feature.chroma_cens(y=y_harmonic, sr=sr)
        
        # 時間軸に沿って最も強い音を検出
        # フレーム単位だと細かすぎるので、ある程度まとめる
        frames = chroma.shape[1]
        time_step = 0.5 # 0.5秒ごとに解析
        samples_per_step = int(time_step * (sr / 512)) # hop_length=512想定
        
        chord_sequence = []
        duration = librosa.get_duration(y=y, sr=sr)
        
        for t in np.arange(0, duration, time_step):
            # 時間 t に対応するフレームインデックス
            idx = int(t * (sr / 512))
            if idx >= frames: break
            
            # 周辺フレームの平均をとる
            end_idx = min(idx + 10, frames)
            segment = chroma[:, idx:end_idx]
            if segment.size == 0: continue
            
            avg_chroma = np.mean(segment, axis=1)
            root_idx = np.argmax(avg_chroma)
            chord_name = AudioPostProcessor.CHORD_NAMES[root_idx]
            
            # 重複排除してリストに追加
            timestamp = f"{int(t//60):02}:{int(t%60):02}"
            chord_sequence.append(f"[{timestamp}] {chord_name}")

        return chord_sequence

    @staticmethod
    def process_file(file_path, output_dir, add_click=False, speed=1.0, pitch_semitones=0.0, analyze_chord=False, progress_callback=None):
        """
        ファイルを読み込み、ピッチ変更 -> タイムストレッチ -> クリック追加 -> コード解析 -> 保存
        """
        try:
            if progress_callback: progress_callback("Loading Audio...")
            y, sr = librosa.load(file_path, sr=None)

            # 1. 無音カット
            if progress_callback: progress_callback("Trimming Silence...")
            y, _ = librosa.effects.trim(y, top_db=30)

            # 2. ピッチシフト (速度を変えずに音程を変える)
            # ※処理が重いため、変更がある場合のみ実行
            if pitch_semitones != 0.0:
                if progress_callback: progress_callback(f"Applying Pitch Shift ({pitch_semitones:+.1f})...")
                # n_steps: 半音単位 (正=上げ, 負=下げ)
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_semitones)

            # 3. タイムストレッチ (音程を変えずに速度を変える)
            if speed != 1.0:
                if progress_callback: progress_callback(f"Applying Time Stretch ({speed:.2f}x)...")
                y = librosa.effects.time_stretch(y, rate=speed)

            # 4. コード解析 (オプション)
            chords_result = []
            if analyze_chord:
                if progress_callback: progress_callback("Analyzing Chords...")
                chords_result = AudioPostProcessor.estimate_chords(y, sr)

            # 5. クリック音の追加
            if add_click:
                if progress_callback: progress_callback("Analyzing BPM...")
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                if isinstance(tempo, np.ndarray):
                    tempo = tempo[0]
                if tempo <= 0: tempo = 120 
                
                if progress_callback: progress_callback(f"Generating Click (BPM: {int(tempo)})...")
                
                # 再生速度が変わっている場合、BPMも変わるため補正して表示用に使用するが
                # ここでは波形結合なので、現在の波形に対してBPM解析すれば正しい
                
                beat_duration = 60 / tempo
                beat_samples = int(beat_duration * sr)
                
                pre_count = AudioPostProcessor.create_click_track(tempo, sr, beat_duration * 5, 4)
                pre_count = pre_count[:beat_samples*4]
                
                y = np.concatenate([pre_count, y])

            # 6. 保存
            if progress_callback: progress_callback("Saving File...")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            filename = os.path.splitext(os.path.basename(file_path))[0]
            
            # ファイル名サフィックス作成
            suffix = ""
            if speed != 1.0: suffix += f"_x{speed:.2f}"
            if pitch_semitones != 0.0: suffix += f"_{pitch_semitones:+.1f}st"
            if add_click: suffix += "_Click"
            
            save_path = os.path.join(output_dir, f"{filename}{suffix}.wav")
            
            sf.write(save_path, y, sr)
            
            return save_path, chords_result

        except Exception as e:
            raise e