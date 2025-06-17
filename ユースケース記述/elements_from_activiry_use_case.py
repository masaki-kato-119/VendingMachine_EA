import xml.etree.ElementTree as ET
import re
import io

def get_tagged_value(element, ns, tag_name):
    tagged_values = element.findall(f'.//UML:ModelElement.taggedValue/UML:TaggedValue', ns)
    for tv in tagged_values:
        if tv.get('tag') == tag_name:
            return tv.get('value')
    return None

def parse_activity_diagram_xmi_final_v3(input_file_path, output_file_path):
    """
    【最終修正版 v3】
    ActionPin, ObjectNode, Activityなど、すべての要素タイプに対応。
    """
    try:
        with open(input_file_path, 'rb') as f:
            xml_bytes = f.read()
        xml_text = xml_bytes.decode('shift_jis')
        xml_text = re.sub(r'encoding=[\'"].*?[\'"]', 'encoding="UTF-8"', xml_text, count=1)
        xml_bytes_utf8 = xml_text.encode('utf-8')
        tree = ET.parse(io.BytesIO(xml_bytes_utf8))
        root = tree.getroot()
    except FileNotFoundError:
        print(f"エラー: ファイル '{input_file_path}' が見つかりません。")
        return
    except Exception as e:
        print(f"XMLの解析中にエラーが発生しました: {e}")
        return

    ns = {'UML': 'omg.org/UML1.3'}
    elements = {}
    partitions = {}

    # --- ステップ1: 要素収集 ---
    # 検索対象にUML:ClassifierRoleを追加
    all_diagram_elements = (root.findall('.//UML:ActionState', ns) + 
                            root.findall('.//UML:PseudoState', ns) + 
                            root.findall('.//UML:ClassifierRole', ns))
    
    for elem in all_diagram_elements:
        elem_id = elem.get('xmi.id')
        if not elem_id:
            continue

        elem_type = get_tagged_value(elem, ns, 'ea_stype')
        name = elem.get('name')
        
        # タイプに基づいた処理
        if elem_type == 'ActivityPartition':
            part_name = get_tagged_value(elem, ns, 'classname')
            elements[elem_id] = {'name': part_name, 'type': 'Partition'}
            partitions[elem_id] = {'name': part_name, 'actions': []}
        elif elem_type in ['Action', 'Activity']: # Activityもアクションとして扱う
            owner_id = get_tagged_value(elem, ns, 'owner')
            elements[elem_id] = {'name': name, 'type': 'Action', 'owner': owner_id}
        elif elem_type == 'Decision':
            elements[elem_id] = {'name': name, 'type': 'Decision'}
        # ActionPinとObjectNodeを新たに追加
        elif elem_type in ['ActionPin', 'ObjectNode']:
            elements[elem_id] = {'name': name, 'type': elem_type}
        elif elem_type in ['StateNode', 'MergeNode']:
             elements[elem_id] = {'name': name or elem_type, 'type': elem_type} # 名前がなければタイプ名を入れる

    # --- ステップ2: アクションの割り当て ---
    for elem_id, elem_data in elements.items():
        if elem_data.get('type') == 'Action' and elem_data.get('owner'):
            owner_id = elem_data.get('owner')
            if owner_id in partitions:
                partitions[owner_id]['actions'].append(elem_data['name'])

    # --- ステップ3: フロー抽出 ---
    flows = []
    for trans in root.findall('.//UML:StateMachine.transitions/UML:Transition', ns):
        source_id = trans.get('source')
        target_id = trans.get('target')
        source_name = elements.get(source_id, {}).get('name', f"ID不明({source_id})")
        target_name = elements.get(target_id, {}).get('name', f"ID不明({target_id})")
        condition = None
        guard = trans.find('.//UML:Guard/UML:Guard.expression/UML:BooleanExpression', ns)
        if guard is not None:
            condition = guard.get('body')
        flows.append({'source': source_name, 'target': target_name, 'condition': condition})
        
    # --- 結果出力 ---
    output_lines = []
    output_lines.append("### 自動販売機システム アクティビティ図 ###")
    output_lines.append("\n--- 1. パーティションとアクション ---")
    if partitions:
        for part_id, part_data in sorted(partitions.items(), key=lambda item: item[1]['name']):
            output_lines.append(f"\n【パーティション】: {part_data['name']}")
            valid_actions = [action for action in part_data['actions'] if action is not None]
            if not valid_actions:
                output_lines.append("  (名前付きのアクションはありません)")
            else:
                for action in sorted(valid_actions):
                    output_lines.append(f"  - {action}")
    else:
        output_lines.append("パーティションが見つかりませんでした。")
        
    output_lines.append("\n--- 2. 分岐 (Decision) ---")
    decision_lines = [elem_data['name'] for elem_data in elements.values() if elem_data.get('type') == 'Decision' and elem_data.get('name')]
    if not decision_lines:
        output_lines.append("分岐が見つかりませんでした。")
    else:
        for line in sorted(decision_lines):
            output_lines.append(f"- {line}")

    output_lines.append("\n--- 3. フロー (矢印) ---")
    if flows:
        sorted_flows = sorted(flows, key=lambda x: (str(x['source']), str(x['target'])))
        for flow in sorted_flows:
            if flow['source'] is None or flow['target'] is None: continue
            flow_str = f"- フロー: 「{flow['source']}」→「{flow['target']}」"
            if flow['condition']:
                flow_str += f" [条件: {flow['condition']}]"
            output_lines.append(flow_str)
    else:
        output_lines.append("フローが見つかりませんでした。")

    final_output = "\n".join(output_lines)
    print(final_output)
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_output)
        print(f"\n--- 結果は '{output_file_path}' に保存されました。 ---")
    except Exception as e:
        print(f"\n--- ファイルへの保存中にエラーが発生しました: {e} ---")
# --- メインの実行部分 ---
if __name__ == '__main__':
    # 入力ファイルと出力ファイルを指定
    input_xml_file = './vendingmachine_ea/ユースケース記述/商品一覧を表示する.xml'
    output_text_file = './vendingmachine_ea/ユースケース記述/商品一覧を表示する_アクティビティ図.md'
    parse_activity_diagram_xmi_final_v3(input_xml_file, output_text_file)
