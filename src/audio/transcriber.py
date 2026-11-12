import os
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

class AudioTranscriber:
    @staticmethod
    def audio_to_midi(audio_path, output_dir, log_callback=None):
        """
        Basic Pitchを使用して音声をMIDIに変換する。
        """
        try:
            if log_callback: log_callback("Loading AI Model (Basic Pitch)...")
            
            # 出力ファイルの設定
            filename = os.path.splitext(os.path.basename(audio_path))[0]
            output_midi_path = os.path.join(output_dir, f"{filename}_Detected.mid")
            
            if log_callback: log_callback("Analyzing Audio & Generating MIDI...")
            
            # ▼▼▼ 修正: model_or_model_path 引数を追加 ▼▼▼
            predict_and_save(
                audio_path_list=[audio_path],
                output_directory=output_dir,
                save_midi=True,
                sonify_midi=False,
                save_model_outputs=False,
                save_notes=False,
                model_or_model_path=ICASSP_2022_MODEL_PATH
            )
            # ▲▲▲ 修正終了 ▲▲▲
            
            # basic-pitchはファイル名を自動生成するため、リネーム処理が必要
            # デフォルトでは `{元のファイル名}_basic_pitch.mid` になる
            expected_output = os.path.join(output_dir, f"{filename}_basic_pitch.mid")
            
            if os.path.exists(expected_output):
                # わかりやすい名前にリネーム
                if os.path.exists(output_midi_path):
                    os.remove(output_midi_path)
                os.rename(expected_output, output_midi_path)
                return output_midi_path
            
            return expected_output

        except Exception as e:
            # 詳細なエラー情報を出すためにそのままraise
            raise RuntimeError(f"Transcription failed: {e}")