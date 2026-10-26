from src.json_repair.json_repair import repair_json


def test_parse_comment():
    assert repair_json("/") == ""
    assert repair_json('/* comment */ {"key": "value"}')
    assert repair_json('{ "key": { "key2": "value2" // comment }, "key3": "value3" }') == '{"key": {"key2": "value2"}}'
    assert (
        repair_json('{ "key": { "key2": "value2" // comment\n}, "key3": "value3" }')
        == '{"key": {"key2": "value2"}, "key3": "value3"}'
    )
    assert (
        repair_json('{ "key": { "key2": "value2" # comment }, "key3": "value3" }')
        == '{"key": {"key2": "value2"}, "key3": "value3"}'
    )
    assert (
        repair_json('{ "key": { "key2": "value2" /* comment */ }, "key3": "value3" }')
        == '{"key": {"key2": "value2"}, "key3": "value3"}'
    )
    assert repair_json('[ "value", /* comment */ "value2" ]') == '["value", "value2"]'
    assert repair_json('{ "key": "value" /* comment') == '{"key": "value"}'


def test_line_comment_brackets_do_not_trigger_empty_object_array_fallback():
    repaired, logs = repair_json("{\n// comment ]\n}", return_objects=True, skip_json_loads=True, logging=True)

    assert repaired == {}
    assert all("try to parse this as an array instead" not in entry["text"] for entry in logs)


def test_block_comment_brackets_do_not_trigger_empty_object_array_fallback():
    repaired, logs = repair_json("{/* comment ] */}", return_objects=True, skip_json_loads=True, logging=True)

    assert repaired == {}
    assert all("try to parse this as an array instead" not in entry["text"] for entry in logs)


def test_line_comment_brackets_do_not_close_array_items():
    raw = """
    {
        "Changes": [
            //object a
            {
                "Action": "1"
            },
            //object b ]
            {
                "Action": "2"
            },
            //object c ]
            {
                "Action": "3"
            }
        ]
    }
    """

    assert repair_json(raw, return_objects=True, skip_json_loads=True) == {
        "Changes": [{"Action": "1"}, {"Action": "2"}, {"Action": "3"}]
    }


def test_parse_many_top_level_comments_without_recursion_error():
    comment_count = 600
    raw = ("# comment\n" * comment_count) + '{"key": "value"}'

    repaired, logs = repair_json(raw, return_objects=True, skip_json_loads=True, logging=True)

    assert repaired == {"key": "value"}
    assert len(logs) == comment_count
    assert all(log["text"] == "Found line comment: # comment, ignoring" for log in logs)


def test_parse_comment_between_colon_and_value():
    assert repair_json('{"a": /* comment */ 1}') == '{"a": 1}'
    assert repair_json('{"a": // comment\n "x", "b": 2}') == '{"a": "x", "b": 2}'
    assert repair_json('{"a": # comment\n true}') == '{"a": true}'
    assert repair_json('{"a": /* comment */ {"b": 1}}') == '{"a": {"b": 1}}'
    assert repair_json('{"a": /* comment */ [1, 2]}') == '{"a": [1, 2]}'
    assert repair_json('{"a": /* one */ /* two */ 2, "b": 3}') == '{"a": 2, "b": 3}'
    assert repair_json('{"a": /* comment */}') == '{"a": ""}'
