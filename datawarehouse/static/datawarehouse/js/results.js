// This file contains javascript functions used by the results page.

// This function is responsible for setting up the dataTables instance.
// dataTables is a jquery library that creates dynamic tables with
// sorting, searching, and column selection, among other features
function resultsLoad() {
    $('#resultsTable').dataTable({
        "bDestroy": true,
        "sPaginationType": "full_numbers",
        "sDom": 'T<"clear">lfrtip',
        "oTableTools": {
	    "sSwfPath": "/static/datawarehouse/TableTools/media/swf/copy_csv_xls_pdf.swf"
	},
        "oLanguage": {                                          // changes html elements defined by dataTables
            "sLengthMenu": "Number of records _MENU_ "          // Change the way the select box is displayed
        }
    });
    
    $('.toggleBox').attr('checked','checked');                  // check the toggle boxes on page load or reload which 
                                                                // ensures displayed columns correspond to checked boxes
}

// This function is used to change the visibility of columns in the data table
function fnShowHide( iCol )
{
    var oTable = $('#resultsTable').dataTable();                // Get the DataTables object 
    var bVis = oTable.fnSettings().aoColumns[iCol].bVisible;    // get the current visibility of the object
    oTable.fnSetColumnVis( iCol, bVis ? false : true );         // change the visibility
}

// This function is used to collapse and expand the toggle buttons div
$('.toggleTitle').live('click', function(){
    $('.toggleButtons').slideToggle('slow');
});
