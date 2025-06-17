import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import io

def extract_requirement_info_from_xmi(file_path):
    """
    Enterprise Architectの要求図XMIから要求と関連を抽出します。
    ファイルはShift_JISとして読み込み、内部でUTF-8に変換して処理します。

    Args:
        file_path (str): 解析対象のXMIファイルのパス。

    Returns:
        tuple: (requirements, relationships) のタプル。
               requirementsはIDをキーとする辞書、relationshipsは関連のリスト。
    """
    requirements = {}
    relationships = []

    try:
        namespaces = {'UML': 'omg.org/UML1.3'}

        # ご指定の文字コード処理方法を適用
        # Shift_JISでバイナリ読み込み
        with open(file_path, 'rb') as f:
            xml_bytes = f.read()
        # Shift_JIS→UTF-8へ変換
        xml_text = xml_bytes.decode('shift_jis')
        # encoding宣言を正規表現でUTF-8に置換
        xml_text = re.sub(r'encoding=[\'"].*?[\'"]', 'encoding="UTF-8"', xml_text, count=1)
        # UTF-8バイト列に再エンコード
        xml_bytes_utf8 = xml_text.encode('utf-8')
        # メモリ上のバイトデータからXMLをパース
        tree = ET.parse(io.BytesIO(xml_bytes_utf8))
        root = tree.getroot()
        print("step1")
        # Step 1: 要求要素（ClassifierRole）をすべて抽出
        for req in root.findall('.//UML:ClassifierRole', namespaces):
            stereotype = req.find('.//UML:Stereotype', namespaces)
            if stereotype is not None and stereotype.get('name') == 'requirement':
                xmi_id = req.get('xmi.id')
                name = req.get('name')
                if xmi_id and name:
                    requirements[xmi_id] = {'name': name, 'id': None, 'text': ''}

        print("step2")
        # Step 2: 要求のIDとテキスト（メモ）を抽出し、結合
        for tv in root.findall('.//UML:TaggedValue', namespaces):
            model_element_id = tv.get('modelElement')
            if model_element_id in requirements:
                tag = tv.get('tag')
                value = tv.get('value')
                if tag == 'id':
                    requirements[model_element_id]['id'] = value
                elif tag == 'text' and value:
                    clean_text = re.sub(r'^<memo>#NOTES#', '', value).strip()
                    requirements[model_element_id]['text'] = clean_text
        
        print("step3")
        # Step 3: 要求間の関連（DependencyとAssociation）を抽出
        # Dependency (deriveReqt, refineなど)
        for dep in root.findall('.//UML:Dependency', namespaces):
            stereotype_element = dep.find('.//UML:Stereotype', namespaces)
            if stereotype_element is not None:
                rel_type = stereotype_element.get('name')
                tagged_values = {
                    tv.get('tag'): tv.get('value')
                    for tv in dep.findall('.//UML:TaggedValue', namespaces)
                }
                source_name = tagged_values.get('ea_sourceName')
                target_name = tagged_values.get('ea_targetName')
                if source_name and target_name:
                    relationships.append((source_name, rel_type, target_name))

        print("Association")
        # Association (Nestingなど)
        for assoc in root.findall('.//UML:Association', namespaces):
            tagged_values = {
                tv.get('tag'): tv.get('value')
                for tv in assoc.findall('.//UML:TaggedValue', namespaces)
            }
            rel_type = tagged_values.get('ea_type')
            source_name = tagged_values.get('ea_sourceName')
            target_name = tagged_values.get('ea_targetName')
            if rel_type and source_name and target_name:
                relationships.append((source_name, rel_type, target_name))

        return requirements, relationships

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {file_path}")
        return None, None
    except ET.ParseError as e:
        print(f"エラー: XMLの解析に失敗しました: {file_path} - {e}")
        return None, None
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return None, None

# --- スクリプトの実行 ---
if __name__ == "__main__":
    input_xmi_file = './vendingmachine_ea/要求図/要求図.xml'
    output_markdown_file = './vendingmachine_ea/要求図/要求図_要素.md'
    
    requirements_dict, relationships_list = extract_requirement_info_from_xmi(input_xmi_file)

    print(requirements_dict)
    print(relationships_list)

    if requirements_dict and relationships_list:
        # ファイルに出力する文字列を組み立てる
        output_lines = []
        output_lines.append("### 自動販売機システム 要求分析レポート ###\n")
        # 1. 要求一覧をテーブル形式で追加
        output_lines.append(f"## 1. 要求一覧 ({len(requirements_dict)}件)\n")
        output_lines.append("| ID | 要求名 | 要求テキスト |")
        output_lines.append("|----|----------|----------|")
        sorted_reqs = sorted(requirements_dict.values(), key=lambda x: (x.get('id') or ''))
        for req in sorted_reqs:
            req_id = req.get('id', 'N/A')
            req_name = req.get('name', '')
            req_text = req.get('text', '')
            output_lines.append(f"| {req_id} | {req_name} | {req_text} |")
        output_lines.append("\n---\n")

        # 2. 関連を種類ごとにグループ化して追加
        output_lines.append(f"## 2. 要求の関連 ({len(relationships_list)}件)\n")
        
        grouped_rels = defaultdict(list)
        for source, rel_type, target in relationships_list:
            grouped_rels[rel_type].append((source, target))
            
        for rel_type in sorted(grouped_rels.keys()):
            output_lines.append(f"### 関連タイプ: `{rel_type}`")
            for source, target in sorted(grouped_rels[rel_type]):
                output_lines.append(f"- **{source}** → **{target}**")
            output_lines.append("") # 改行
        output_lines.append("---\n")
        
        print("組み立てた文字列をファイルに書き込む")
        # 組み立てた文字列をファイルに書き込む
        try:
            with open(output_markdown_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(output_lines))
            print(f"成功: レポートが '{output_markdown_file}' に出力されました。")
        except IOError as e:
            print(f"エラー: ファイルの書き込みに失敗しました: {e}")