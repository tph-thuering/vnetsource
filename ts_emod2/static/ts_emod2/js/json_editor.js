$(document).ready(function()
{
    var json_textarea = $('#json');

    json_textarea.text(JSON.stringify(json, null, 4));

    editor = CodeMirror.fromTextArea(document.getElementById("json"),
    {
        lineNumbers: true,
        matchBrackets: true
    });

    window.jsoneditor = editor;
});

function undo()
{
    window.jsoneditor.undo();
}

function redo()
{
     window.jsoneditor.redo();
}

function cancel()
{
    window.history.back();
}