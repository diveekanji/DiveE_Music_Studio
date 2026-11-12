import os
from pathlib import Path

# 除外設定 (ノイズ除去とセキュリティ確保)
IGNORE_DIRS = {
    '.git', '.venv', '__pycache__', 'dist', 'build', 
    'DiveE_Exports', 'Output', 'temp_downloads', 'gp_processing_temp',
    '_internal'
}
IGNORE_EXTS = {
    '.pyc', '.pyd', '.exe', '.dll', '.so', '.dylib', '.zip', '.pdf', 
    '.mp3', '.wav', '.mp4', '.mid', '.midi', '.png', '.jpg', '.ico',
    '.lock'
}
IGNORE_FILES = {
    'client_secrets.json', 'songsterr_auth.json', 'token_gmail.pickle', 
    'dump_for_gem.py', 'poetry.lock', 'uv.lock'
}

def dump_project(output_file="DiveE_Source_Code.txt"):
    root_path = Path.cwd()
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"Project Name: DiveE MUSIC STUDIO\n")
        out.write(f"Root Path: {root_path}\n")
        out.write("="*60 + "\n\n")

        for root, dirs, files in os.walk(root_path):
            # 除外ディレクトリをスキップ
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES: continue
                if any(file.endswith(ext) for ext in IGNORE_EXTS): continue
                
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)
                
                out.write(f"FILE_PATH: {rel_path}\n")
                out.write("-" * 30 + "\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        out.write(content + "\n")
                except Exception as e:
                    out.write(f"[Error reading file: {e}]\n")
                
                out.write("\n" + "="*60 + "\n\n")
    
    print(f"完了しました。生成された '{output_file}' をGEMにアップロードしてください。")

if __name__ == "__main__":
    dump_project()