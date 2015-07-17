/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/

/* This function uses an ajax request to get the specified table's data. It then creates
 * a Datatables DOM element for the data. It also creates checkboxes to select/deselect
 * columns. */
function getTable(lut) {
    var url = "api/Lookup/" + lut + "/?format=json";
    var lutElement = '#' + lut + "Table";
    var ludata = [];
    $('#loading-indicator').show();

    $.get(url, function (data) {
        ludata = data["objects"];
        if (ludata != "") {
            var tmparr = [];
            var luarr = [];
            var luColumns = [];
            var current_order = [];
            var col_order = [];
            var order_array = [];

            $.each(ludata[0], function (key, value) {
                if (value != null && typeof value == 'object') {
                    $.each(value, function (k) {
                        if (k == "resource_uri") {
                            luColumns.push({"sTitle": beautify(key + " " + k)});
                            current_order.push(key + "_" + k);
                        }
                        else if (k != "field_order") {
                            luColumns.push({"sTitle": beautify(k)});
                            current_order.push(k);
                        }
                        else {
                            order_array = value.split(",");
                        }
                    });
                }
                else {
                    if (key == "resource_uri") {
                        luColumns.push({"sTitle": beautify(lut + " " + key)});
                        current_order.push(lut + "_" + key);
                    }
                    else if (key != "field_order") {
                        luColumns.push({"sTitle": beautify(key)});
                        current_order.push(key);
                    }
                    else {
                        order_array = value.split(",");
                    }
                }
            });
            $.each(ludata, function (item) {
                $.each(ludata[item], function (key, value) {
                    if (value != null && typeof value == 'object') {
                        $.each(value, function (k, v) {
                            tmparr.push(v);
                        });
                    }
                    else if (key != "field_order") {
                        tmparr.push(value);
                    }
                });
                luarr.push(tmparr);
                tmparr = []
            });
            col_order = get_ordering(current_order, order_array);
            if (!isDataTable($(lutElement)[0])) {
                createTable(lutElement, luarr, luColumns, col_order);
                createBoxes(luColumns, lut);
                $('#loading-indicator').hide();
            }
            else {
                $('#loading-indicator').hide();
            }
        }
        else {
            $('#loading-indicator').hide();
        }
    });

}

/* This function returns the desired column ordering as an array of integers (the DataTables ColReorder plug-in expects
 an array of integers.) It accepts an array containing the current ordering and an array containing the desired
 ordering (the values in the arrays are strings). It works by first creating a dictionary containing the
 desired ordering string and index, then looping through the current ordering and creating an array of the
 corresponding integer values form the dictionary.
 */
function get_ordering(current, desired) {
    var current_ordering = {};
    var ordering = [];

    for (var i = 0; i < current.length; i++) {
        current_ordering[current[i]] = i;
    }

    for (var j = 0; j < desired.length; j++) {
        ordering.push(current_ordering[desired[j]]);
    }

    return ordering;
}

/* This function creates checkboxes for selecting/deselecting columns in the table.*/
function createBoxes(values, lut) {
    var tbl = document.createElement('table');
    tbl.className = "toggles";
    var row = document.createElement('tr');
    var cell = document.createElement('td');
    var checkbox, label;
    var len = values.length;
    var perColumn;
    if (len % 4 == 0) {
        perColumn = len / 4;
    }
    else {
        perColumn = (len - (len % 4)) / 4 + 1;
    }
    for (var i = 0; i < len; i++) {
        if (i % perColumn == 0) {
            row.appendChild(cell);
            cell = document.createElement('td');
        }
        checkbox = document.createElement('input');
        label = document.createElement('label');
        checkbox.type = "checkbox";
        checkbox.className = "toggleBox";
        checkbox.checked = "true";
        checkbox.setAttribute('onClick', 'fnShowHide("' + lut + 'Table", "' + values[i]["sTitle"] + '")');
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(" " + values[i]["sTitle"]));
        cell.appendChild(label);
    }
    row.appendChild(cell);
    tbl.appendChild(row);
    $("#" + lut + "toggleButtons").append(tbl);
}
/* This function takes a reference to a DOM element and creates a Datatables table
 * in that element. */
function createTable(element, data, columns, order) {
    $(element).dataTable({
        "bSortCellsTop": true,
        "sDom": "R<'row-fluid'<'span4'l><'span4'f><'span3'T>r>Rt<'row-fluid'<'span6'p><'span6'i>>",
        "aaSorting": [
            [order[0], "asc"]
        ],
        "oColReorder": {
            "aiOrder": order
        },
        "aaData": data,
        "aoColumns": columns,
        "sWrapper": "dataTables_wrapper form-inline",
        "sPaginationType": "bootstrap",
        "oTableTools": {
            "sSwfPath": "/static/datawarehouse/TableTools/media/swf/copy_csv_xls_pdf.swf",
            "aButtons": ["copy", "print", "csv", "xls", "pdf"]
        },
        "oLanguage": {                                          // changes html elements defined by dataTables
            "sLengthMenu": "Records/page _MENU_"            // Change the way the select box is displayed
        }
    });
    // Append an image to the table headers to make clear the table can be sorted by column
    $('.lookuptable thead th ').append('<icon class="icon-angle-up"></i>');
}
/* This function tests if a table has been initialised as a DataTables table. */
function isDataTable(nTable) {
    var settings = $.fn.dataTableSettings;
    for (var i = 0, iLen = settings.length; i < iLen; i++) {
        if (settings[i].nTable == nTable) {
            return true;
        }
    }
    return false;
}
/* This runs when the document loads. It checks all boxes, shows the first tab
 * and triggers a click event on the first tab's table. */
$(document).ready(function () {
    $('.toggleBox').attr('checked', 'checked');  // check the toggle boxes on page load or reload which
    // ensures displayed columns correspond to checked boxes
    $('.checkAll').attr('checked', 'checked');  // make sure checkall box is initially checked
    $('#luTables a:first').tab('show');         // show the first tab by
    $('#luTables a:first').trigger('click');
});
// This function is used to change the visibility of columns in the data table
function fnShowHide(selname, iName) {
    var oTable = $('#' + selname).dataTable();                	// Get the DataTables object
    for (var i = 0; i < oTable.fnSettings().aoColumns.length; i++) {
        if (oTable.fnSettings().aoColumns[i].sTitle == iName) {
            var bVis = oTable.fnSettings().aoColumns[i].bVisible;    // get the current visibility of the object
            oTable.fnSetColumnVis(i, bVis ? false : true);      // change the visibility
        }
    }
}
// This function is used to collapse and expand the toggle buttons div
$('.toggleTitle').live('click', function () {
    $('.active .toggleButtons').slideToggle('slow');
});
// This function is used to select all column headings.
$('.checkAll').live('click', function () {
    if ($(this).is(':checked')) {
        $.each($('.active .toggleBox '), function () {
            if ($(this).is(':checked')) {
                return
            }
            else {
                $(this).trigger('click');
            }
        });
    }
    else {
        $.each($('.active .toggleBox'), function () {
            if ($(this).is(':checked')) {
                $(this).trigger('click');
            }
        });
    }
});

$.extend($.fn.dataTableExt.oStdClasses, {
    "sSortAsc": "header headerSortDown",
    "sSortDesc": "header headerSortUp",
    "sSortable": "header"
});
/* Capitalized all of the words in a string seperated by whitespace
 *
 * Input arguments
 *  in_string:      The string that is to be capitalized
 *
 * Output arguments
 *  out_string:     The capitalized string*/
function capitalize(in_string) {
    var out_string = in_string.toLowerCase().replace(/\b[a-z]/g, function (letter) {
        return letter.toUpperCase();
    });
    return out_string;
}

/* This is used to make the measure names in the Vecnet project human readable
 * It replaces all underscores with spaces and certain words with their symbols
 * ex: percent becomes %.  This allows for nice looking names while allowing the
 * actual measure name to be used for jquery selection and data passing
 *
 * Input Arguments:
 *  in_string:      The string to be "beautified"
 *
 * Output Arguments:
 *  in_string:      The beautified string*/
function beautify(in_string) {
    in_string = in_string.replace(/_/g, " ");
    in_string = in_string.replace("percent", "%");
    in_string = in_string.replace("gte", ">=");
    in_string = in_string.replace("number", "#");
    in_string = in_string.replace("years", "yrs");
    in_string = capitalize(in_string);
    return in_string;
}