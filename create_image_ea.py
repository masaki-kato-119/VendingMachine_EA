import win32com.client
import os
import time


def ensure_directory(path):
    """指定されたディレクトリが存在しない場合は作成する"""
    os.makedirs(path, exist_ok=True)


def export_diagram(diagram, output_path):
    """ダイアグラムをPNG形式で保存する"""
    try:
        diagram.SaveImagePage(1, 1, 0, 0, output_path, 1)
        print(f"Exported: {diagram.Name} -> {output_path}")
    except Exception as e:
        print(f"  エラー: {e}")


def process_package(package, base_output_dir):
    """パッケージ内のサブパッケージとダイアグラムを処理する"""
    for sub_package in package.Packages:
        output_dir = os.path.join(base_output_dir, sub_package.Name)
        ensure_directory(output_dir)
        for diagram in sub_package.Diagrams:
            diagram_name = diagram.Name.replace(" ", "_")
            output_path = os.path.join(output_dir, f"{diagram_name}.PNG")
            export_diagram(diagram, output_path)


def export_diagrams_from_ea(ea_file_path):
    """EAファイルからダイアグラムをPNG形式で出力する"""
    ea_app = win32com.client.Dispatch("EA.App")
    repository = ea_app.Repository
    repository.OpenFile(ea_file_path)

    try:
        for root_package in repository.Models:
            for package in root_package.Packages:
                process_package(package, os.getcwd())
    finally:
        repository.CloseFile()
        repository.Exit()
        del repository
        del ea_app


def main():
    ea_filename = "自動販売機.qea"
    ea_file_path = os.path.join(os.getcwd(), ea_filename)

    start_time = time.time()
    export_diagrams_from_ea(ea_file_path)
    elapsed = time.time() - start_time

    print(f'実行時間: {elapsed:.2f} 秒')


if __name__ == '__main__':
    main()