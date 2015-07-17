// page_name and data_to_save are pulled in from the class including this file

function save_data(post_type)
{
    var the_url = "/ts_repr/" + page_name + "/save_data/";
    var type = post_type;

    $.ajax(
    {
        data: JSON.stringify(data_to_save),
        type: "POST",
        url: the_url,

        success: function(representative_id)
        {
            $('#representative_id').val(representative_id); // This is for new_scenario page only.

            if (type == 'save_and_continue')
            {
                $('#form').submit();
            }
        },

        error: function(XMLHttpRequest, textStatus, errorThrown)
        {
            alert("Status: " + textStatus); alert("Error: " + errorThrown);
        }
    });
}