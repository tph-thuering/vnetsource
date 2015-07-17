/*######################################################################################################################
 # VECNet CI - Prototype
 # Date: 4/16/2013
 # Institution: University of Notre Dame
 # Primary Authors:
 #   Gregory Davis <gdavis2@nd.edu>
 ######################################################################################################################*/
/* Javascript for ts_emod/views/BrowseView - based on openmalaria */

/* Method to be executed when page has been loaded */
$(document).ready(function(){

    /* handle changing the maximum number of results to display on a page (paging option) */
    $("input[name=limit_size]").change(function () {
        $('#pager_size').val($(this).val());
        $('#pager_form').submit();
    });

    /* handle filtering visible items by owner (paging option) */
    $("input[name=display_group]").change(function () {
        $('#scenario_display').val($(this).val());
        $('#pager_form').submit();
    });

    /* Handle UI request to delete an item. Show dialog confirming action */
    $('a.btn-delete').click( function(e){
        var link = this;
        e.preventDefault();
        $("<div><p>You are about to permanently delete this item. This action cannot be undone.</p><p>Are you sure you want to continue?</p></div>").dialog({
            title: 'Deletion Warning!',dialogClass: "no-close", draggable: false, resizable: false, class: 'alert', modal: true,
            buttons: {
                "Cancel": { text: 'Cancel', priority: 'primary', class: 'btn', click: function(){ $(this).dialog("close"); } },
                "Ok": { text: 'Ok', priority: 'secondary', class: 'btn btn-danger', click:function() { window.location = link.href; } }
            }
        });
    });
});

/* handles paging requests */
function goToPage(page_num){
    $('#pager_offset').val(page_num);
    $('#pager_form').submit();
}
