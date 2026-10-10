from backend.content import load_all
from backend.decision import Question, decide, export_report


def test_retrieval_export_uses_retrieval_adaptation_categories():
    result = decide(Question(question='关键词 检索', cluster='retrieval'), [c.model_dump() for c in load_all()])
    report, md = export_report(result, ['keyword-retrieval'])
    assert '召回与排序' in report['implementation_modules']
    assert '外部副作用适配' not in report['implementation_modules']
    assert '坏内容保留旧可用索引' in md
