import xml.etree.ElementTree as ET
from collections import defaultdict
import io
import re

def extract_use_case_info_from_xmi(file_path):
    """
    Enterprise ArchitectのXMIファイルからアクター、ユースケース、システム境界、
    およびアクターとユースケースの関連を抽出します。

    Args:
        file_path (str): 解析対象のXMIファイルのパス。

    Returns:
        tuple: (actors, use_cases, system_boundary, associations) のタプル。
               actorsとuse_casesは名前のリスト、system_boundaryは名前の文字列、
               associationsは(actor_name, use_case_name)のタプルのリスト。
    """
    actors = []
    use_cases = []
    system_boundary = None
    associations = []

    try:
        # XMIファイル内の名前空間を登録します
        namespaces = {'UML': 'omg.org/UML1.3'}

        # Shift_JISでバイナリ読み込み
        with open(file_path, 'rb') as f:
            xml_bytes = f.read()
        # Shift_JIS→UTF-8へ変換
        xml_text = xml_bytes.decode('shift_jis')
        # encoding宣言を正規表現で完全に置換
        xml_text = re.sub(r'encoding=[\'"].*?[\'"]', 'encoding="UTF-8"', xml_text, count=1)
        # UTF-8バイト列に再エンコード
        xml_bytes_utf8 = xml_text.encode('utf-8')
        # BytesIOでパース
        tree = ET.parse(io.BytesIO(xml_bytes_utf8))
        root = tree.getroot()

        # --- アクターとユースケースの抽出 (前回と同様) ---
        for actor in root.findall('.//UML:Actor', namespaces):
            if 'name' in actor.attrib:
                actors.append(actor.attrib['name'])
        for use_case in root.findall('.//UML:UseCase', namespaces):
            if 'name' in use_case.attrib:
                use_cases.append(use_case.attrib['name'])
        
        # --- システム境界の抽出 (前回と同様) ---
        for classifier in root.findall('.//UML:ClassifierRole', namespaces):
            for tagged_value in classifier.findall('.//UML:TaggedValue', namespaces):
                if tagged_value.get('tag') == 'ea_stype' and tagged_value.get('value') == 'Boundary':
                    if 'name' in classifier.attrib:
                        system_boundary = classifier.attrib['name']
                        break
            if system_boundary:
                break
        
        # --- ★★★ アクターとユースケースの関連を抽出 (新規追加) ★★★ ---
        for assoc in root.findall('.//UML:Association', namespaces):
            tagged_values = {
                tv.get('tag'): tv.get('value')
                for tv in assoc.findall('.//UML:TaggedValue', namespaces)
            }
            
            source_type = tagged_values.get('ea_sourceType')
            target_type = tagged_values.get('ea_targetType')
            source_name = tagged_values.get('ea_sourceName')
            target_name = tagged_values.get('ea_targetName')
            
            # アクターとユースケース間の関連のみを抽出
            if source_type == 'Actor' and target_type == 'UseCase':
                associations.append((source_name, target_name))
            # 逆方向の関連も考慮
            elif source_type == 'UseCase' and target_type == 'Actor':
                associations.append((target_name, source_name))
                
        # 重複を排除してソート
        actors = sorted(list(set(actors)))
        use_cases = sorted(list(set(use_cases)))
        associations = sorted(list(set(associations)))

        return actors, use_cases, system_boundary, associations

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return None, None, None, None
    except ET.ParseError:
        print(f"エラー: XMLの解析に失敗しました: {file_path}")
        return None, None, None, None

# --- スクリプトの実行 ---
if __name__ == "__main__":
    xmi_file_path = './vendingmachine_ea/ユースケース図/ユースケース図.xml'
    
    actors_list, use_cases_list, boundary_name, associations_list = \
        extract_use_case_info_from_xmi(xmi_file_path)

    output_lines = []
    output_lines.append("### 自動販売機システム ユースケース分析 ###\n")

    if boundary_name:
        output_lines.append(f"## 1. システム境界\n")
        output_lines.append(f"- **システム名**: {boundary_name}\n")
        output_lines.append("---\n")

    if actors_list:
        output_lines.append(f"## 2. アクター ({len(actors_list)}件)\n")
        for actor in actors_list:
            output_lines.append(f"- {actor}")
        output_lines.append("\n---\n")
    
    if use_cases_list:
        output_lines.append(f"## 3. ユースケース ({len(use_cases_list)}件)\n")
        for use_case in use_cases_list:
            output_lines.append(f"- {use_case}")
        output_lines.append("\n---\n")

    if associations_list:
        output_lines.append(f"## 4. アクターとユースケースの関連\n")
        
        # アクターをキーとしてユースケースをグループ化
        actor_to_uc_map = defaultdict(list)
        for actor, use_case in associations_list:
            actor_to_uc_map[actor].append(use_case)
            
        # アクターごとに整形して出力
        for actor in sorted(actor_to_uc_map.keys()):
            output_lines.append(f"### アクター: {actor}")
            for use_case in sorted(actor_to_uc_map[actor]):
                output_lines.append(f"- {use_case}")
            output_lines.append("") # アクターごとに改行
        output_lines.append("---\n")

    # ファイル出力
    output_file = "./vendingmachine_ea/ユースケース図/ユースケース図_要素.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(output_lines))

    # 標準出力にも表示（任意）
    print('\n'.join(output_lines))