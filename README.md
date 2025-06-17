# VendingMachine_EA

## 本リポジトリの目的

- 本プロジェクトは、GitHub Copilotを活用し、PlantUMLで検証した自動販売機モデルのモデル検証の自動化を、Enterprise Architect（EA）を用いたSysML版で実現・検証することを目的としています。
- Enterprise ArchitectからXMI形式でモデルを出力し、Pythonスクリプトで図の構成要素を抽出することで、AIによるモデル検証支援の有効性を確認します。
- AIによる支援では、PlantUMLモデルの自動生成と、手動でEAへ反映する運用を想定しています。ただし、PlantUMLの表現力には制約があるため、他の方法も検討していきます。

## 検証用Pythonスクリプト一覧

| スクリプト名 | 概要 |
| --- | --- |
| ai_doc_checker_app.py | EAのダイアグラムからPNGファイルを生成します |
| create_image_ea.py | 検証用プロンプトに従いAIによるモデル検証を実施します |
| ./要求図/elements_from_requirement_diagram.py | 要求図（XMIファイル）から図の構成要素を抽出します |
| ./ユースケース図/elements_from_use_case_diagram.py | ユースケース図（XMIファイル）から図の構成要素を抽出します |
| ./ユースケース記述/elements_from_activiry_use_case.py | アクティビティ図（XMIファイル）から図の構成要素を