/*######################################################################################################################
 # VECNet CI - Prototype
 # Date: 4/5/2013
 # Institution: University of Notre Dame
 # Primary Authors:
 #   Gregory Davis <gdavis2@nd.edu>
 ######################################################################################################################*/
/* Javascript for ts_emod/views/BrowseDetailView - based on openmalaria */

/* Method to be executed when page has been loaded */
$(document).ready(function(){
    // Syntax coloring for pre tags
    prettyPrint();

    /* Ensure that all tooltips are enabled (for this page all <a class="btn-small"> elements) */
    $('a.btn-small').tooltip({container:'body'});

    /* Handle UI request to delete a scenario. Show dialog confirming action */
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

function send_calibration_request()
{
    $("#calibration-request-spinner").hide();
    $("#calibration-request-spinner").show();

    $.ajax
    ({
        data: JSON.stringify(calibration_data),
        type: "POST",
        url: calibration_url,

        success: function ()
        {
            location.reload();
        },

        error: function()
        {
            $("#calibration-request-spinner").hide();
            $("#calibration-request-error").html('<font color="red"> Calibration request failed. </font>');
            $("#calibration-request-error").show();
        }
    });
}