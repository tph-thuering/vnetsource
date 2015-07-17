/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/

// Global variables for UI
var local_cache={};     // Local cache to keep all of the dimension level returns
var charts={};          // Local storage of the chart instances
var yDataButton='';     // Select box code for measure aggregation type
var ajax_call='';       // AJAX call holder.  This willbe used to allow for aborting the call if something happens on the
                        // page.

// Initialization of variables requied by the UI
$(document).ready(function(){
    window.result_object = {};      // Initialize the result object to an empty object. This will be replaced upon a successful slice.
    var chart_data;
    $('#tabList a:first').tab('show');  // Shows the first tab for the tabList

    // We are hiding the visualizer (the div that holds the graphing area and toolbar) and graph_tools upon original navigation
    $('#visualizer').hide();
    $('#graph_tools').hide();

    // Drag and Drop UI initialization
//    $('#visualizer').droppable({
//        drop: handleDropEvent
//    });
//    $('#infocontrol').droppable({
//        drop: RCTDrop
//    });
//    $('#infobar').droppable({
//        drop: RCTDrop
//    });

    $('#xdiv').droppable({
        drop: selectDrop
    });

    $('#ydiv').droppable({
        drop: selectDrop
    });

    $('#Slice_list').droppable({
        drop: sliceDrop
    })


    //Prepare the helpbox
    help_div = document.createElement('div');
    $(help_div).attr('id','tutorial');
    $(help_div).addClass('alert text-center alert-info');
    $(help_div).append('<i class="icon-info-sign"></i>');
    $(help_div).append(' Please Choose a Cube to Begin ');
    $(help_div).append('<a class="close" data-dismiss="alert" herf="#">&times;</a>');
    $('#help_box').append(help_div);
    $('.alert').alert();

    // Get all of the tooltips, bootstrap colorpickers, and other button
    // stuff ready
    $('.dropdown-toggle').dropdown();
    $('#windowbg-cp').colorpicker();
//    $('#windowbg-cp').tooltip();
    $('#windowbrdr-cp').colorpicker();
//    $('#windowbrdr-cp').tooltip();
//    $('#invert').tooltip();
//    $('#spacing').tooltip();
//    $('#plotbg-cp').tooltip();
//    $('#plotbrdr-cp').tooltip();
//    $('.legend-opt').tooltip();
    $('#legendbg-cp').colorpicker();
//    $('#legendbg-cp').tooltip();
    $('#legendbrdr-cp').colorpicker();
//    $('#legendbrdr-cp').tooltip();
//    $('#series-cp').tooltip();
    $('#series-cp').colorpicker();

    //jquery file uploader
    $('#file_upload').fileupload({
        dataType:'json',
        formData:{
            'csrfmiddlewaretoken':csrf_token
        },
        done: function(e, data){
            // First, make sure that the Dataset Selector Tab is showing
            $('[href="#DatasetSel"]').tab('show');

            // Switch to the correct cube
            $('#cube').val(data.result.cube);
            $('#cube').change();

            // Add all dimensions listed in the file
            $('#xdiv .dataset').remove();
            $.each(data.result.dimensions,function(i,val){
                var ui = {};
                var ev = {};
                dim_div = document.createElement('div');
                $(dim_div).addClass('dim ui-draggable');
                $(dim_div).attr('id',val.id).attr('data-kind','dimension').attr('data-levels',val['data-levels']);
                $(dim_div).attr('data-type',beautify(val.id));
                ui['draggable'] = $(dim_div);
                ev['target'] = $('#xdiv');
                selectDrop(ev, ui);
                $('#xdiv .dataset:last-child').children('select').val(val['select-val']);
            });

            // Add all measures in the listed file
            $('#ydiv .dataset').remove();
            $.each(data.result.measures,function(i,val){
                var ui = {};
                var ev = {};
                meas_div = document.createElement('div');
                $(meas_div).addClass('meas ui-draggable');
                $(meas_div).attr('id',val.id).attr('data-kind','measure').attr('data-aggs',val['data-aggs']);
                $(meas_div).attr('data-type',val.id);
                ui['draggable'] = $(meas_div);
                ev['target'] = $('#ydiv');
                selectDrop(ev, ui);
                $('#ydiv .dataset:last-child').children('select').val(val['select-val']);
            });

            // Add all slices
            $('#Slice_list .slice').remove();
            $.each(data.result.slices,function(i,val){
                slice_div = document.createElement('div');
                $(slice_div).addClass('slice text-center');
                $(slice_div).attr('data-dim',val.dimension).attr('data-kind','slice').attr('data-path',val.path);
                $(slice_div).append(val.dimension + ' > ' + val.path);
                var append_text = '<a href="javascript:void(0)" onclick="$(this).parent().remove()"><i class="pull-right icon-remove"></i></a>';
                append_text += '<a href="javascript:void(0)" onclick="editSlice($(this).parent())"><i class="pull-right icon-edit"></i></a>';
                $(slice_div).append(append_text);
                $('#Slice_list').append(slice_div);
            });

            $('#file_upload').hide();
        }
    });

});

// Make it so that panes can dynamically be added or deleted
$('#tabList').on('click','a',function(e){
    e.preventDefault();
    $(this).tab('show');
});
// Cube Select handler code.  
// When the cube is changed, this will get data from the cube to fill the slicing boxes
$('#cube').on('change',function(){
    if($('#cube').val() == 'Default'){return;}
    var value=$(this).val();
    yDataButton='';
    $('#dimensions').empty();
    $('#measures').empty();
//    $('#Slice_list .slice').empty();
    $('.slice').remove();
    $('.dataset').remove();
//    $('#xdiv .dataset').remove();
//    $('#ydiv .dataset').remove();
    $('#RCTCut').children().remove();
    $('#RCTName').children().remove();
    $('#RCTName').append('<h1>Dimension</h1>');
    //$('#DatasetSel').append('<p class="text-info">Drag and drop dimensions and measures here to create a dataset</p>');
    ajax_call = $.getJSON(
        "datawarehouse/SliceBrowser",
        data = {
            "mode":"cube",
            "cube":value
        },
        function(data){
            /*yDataButton += '<select class="span1 pull-right">';
            $.each(data.measure_types,function(key,value){
                yDataButton += '<option val="' + key + '" >' + value + '</option>';;
            });
            yDataButton += '</select>';*/
            processCube(data);
        }
    );
    if($('#tutorial').length > 0){
        $('#tutorial').empty();
        $('#tutorial').append('<i class="icon-info-sign"></i>');
        $('#tutorial').append(' Please select Dimensions and Measures you would like to investigate');
        $('#tutorial').append('<a class="close" data-dismiss="alert" herf="#">&times;</a>');
    }
});

// Process the results from the cube data
// Here we fill all of the dimension and measures boxes with 
// incoming data
function processCube(data){
    // Add to possible aggregation dimensions
    if($('#agg_options p').length > 0){$('#agg_options p').remove();}

    $.each(data.measures,function(key,value){
        var display_text = "<div class='meas' id='" + key + "' data-type='" + value;
        display_text += "' data-aggs='" + data.measure_types[key] + "' data-kind='measure'>"
        display_text += beautify(value);
        display_text += '<a class="pull-right" href="javascript:void(0)" onclick="clickFill(\'measures\',\'' + key +'\')"><i class="icon-plus"></i></a>'; 
        display_text += "</div>"; 
        $('#measures').append(display_text);
        $('#' + key).draggable({
            containment:"window",
            cursor:"move",
            helper:'clone'
        });
    });
    $.each(data.dimensions,function(key,value){
        var display_text = "<div class='dim' id='" + key + "' data-type='" + value;
        display_text += "' data-levels='" + data.levels[key] + "' data-kind='dimension'>"
        display_text += value;
        display_text += '<a class="pull-right" href="javascript:void(0)" onclick="clickFill(\'dimensions\',\'' + key +'\')"><i class="icon-plus"></i></a>'; 
        display_text += "</div>"; 
        $('#dimensions').append(display_text);
        if(data.ranges[key] == 'true'){
            $('#dimensions #' + key).addClass('range');
        }
        $('#' + key).draggable({
            containment:"window",
            cursor:"move",
            helper:'clone'
        });
    });
 
}

/* This function handles adding the dimensions and measures below
 *
 * Due to how the handlers are setup this is a one line function that
 * created the appropriate data given data from the caller
 * Input Arguments:
 *  id_name = Name of the id attribute of the DOM element
 *  parent_name = Name of the parent element of the DOM element*/
function clickFill(parent_name,id_name){
    var ui = [];
    var ev = [];
    var $clone = $('#' + parent_name + ' #' + id_name).clone();
    ui['draggable'] = $clone;
    if($clone.hasClass('meas')){
        ev['target'] = $('#ydiv');
    }else if($clone.hasClass('dim')){
        ev['target'] = $('#xdiv');
    }
    selectDrop(ev,ui);
}

/* This is the drop handler for the slice list
 *
 * This will take a dimension being dropped, open a model and configure said modal.
 * When the modal is "saved", the visible UI element will be appended to the slice
 * list
 *
 * Input Arguments:
 *  event:  This is the jquery drop event (generated by the droppable element)
 *  ui: This is the element that was dropped (ui.draggable)
 */
function sliceDrop(event, ui){
    var draggable = ui.draggable;
    var droppable = event.target;

    if(draggable.hasClass('meas')){
        return;
    }

    $('#sliceModal').modal();

//    $('#RCTName').empty();
    $('#sliceModal .modal-header h3').text('Data Slicer: ' + draggable.attr('data-type'));
    $('#RCTCut').empty();
//    var display_text = "<h1>" + draggable.attr('data-type') + "</h1>";
//    $('#RCTName').append(display_text);

    if(draggable.hasClass('range')){
        $('#RCTCut').append('<div class="span2 pull-left text-center" id="from">From</div>');
        addSelectBox('#from',draggable.attr('id'),0);
        $('#RCTCut').append('<div class="span2 pull-left text-center" id="to">To</div>');
        addSelectBox('#to',draggable.attr('id'),0);
        var display_text = '<button class="btn btn-success slice_button pull-right range" type="button" data-caller="' + draggable.attr('id') + '">';
        display_text += '<i class="icon-arrow-right pull-right"></i></button>';
        $('#RCTCut').append(display_text);
    }
    else{
        // Now that we have the title up, we fill in the drop downs
        addSelectBox('#RCTCut',draggable.attr('id'),0);
    }
}

/* This is the drop handler for dimensions.
 *
 * This checks to see if the draggable element is a dimension, if it is it
 * adds it to the appropriate parent element.  Otherwise the droppable event is
 * dismissed.
 *
 * Input Arguments:
 *  event:  This is the jquery event instance (generated by the droppable class)
 *  ui: This is the element that was dropped
 */
function selectDrop(event, ui){
    var draggable = ui.draggable;
    var droppable = event.target;

    //---------- Make sure the dimensions go to xdiv and the measures to ydiv
    if(($(droppable).attr('id') == "ydiv") && !(draggable.hasClass('meas'))){
        return;
    }

    if(($(droppable).attr('id') == "xdiv") && !(draggable.hasClass('dim'))){
        return;
    }

    //--------- Check to see if the element already exists
    if(($(droppable).children('[data-name=' + draggable.attr('id') + ']').length > 0) && ($(draggable).hasClass('dim'))){
        return;
    }

    var info_div = createDropElement(draggable);

    $(droppable).append(info_div);
}

/* This function handles the creation of the element to place
 *
 * It is passed a DOM element, and from that it will construct the elements 
 * required for the Dimensions and measures elements on the cube browser.
 * 
 * Input Arguments:
 *  baseElement:    This is the element on which to base the new element
 *  
 * Returns:
 *  This returns a DOM element that should be appended to another element
 */
function createDropElement(baseElement, type){
    //----------- Create element
    var info_div = document.createElement('div');
    $(info_div).addClass('dataset text-left');
    $(info_div).attr('id',baseElement.attr('data-type'));
    $(info_div).attr('data-name',baseElement.attr('id'));
    $(info_div).append('<a class="pull-right" href="javascript:void(0)" onclick="$(this).parent().remove()"><i class="icon-remove"></i></a>');
    $(info_div).append(beautify(baseElement.attr('data-type')));

    //----------- Create dropdown for aggregation/
    if(baseElement.hasClass('dim')){
        var level_arr = baseElement.attr('data-levels').split('|');
        if(level_arr.length > 1){
            var level_select = document.createElement('select');
            $(level_select).addClass('span2 pull-right');
            $.each(level_arr,function(index,value){
                $(level_select).append($('<option />').val(value).text(value));
            });
        }
        $(info_div).append(level_select);
    }else if(baseElement.hasClass('meas')){
        // Add the specific select options
        var measure_arr = baseElement.attr('data-aggs').split('|');
        var measure_select = document.createElement('select');
        $(measure_select).addClass('pull-right');
        $.each(measure_arr, function(index, value){
            $(measure_select).append($('<option />').val(value).text(value));
        });
        $(info_div).append(measure_select);
    }
    return info_div;
}

/* This is the drop event handler for the Dataset Selector tab pane
 *
 * When a dimmension or measure are dropped onto the "Dataset Selector" pane
 * of the info bar (middle bar on page) it will create the X and Y dataset dives 
 * if they don't dexist and fill those divs with the appropriate objects (those 
 * dragged from above).  
 *
 * Input Arguments:
 *  event:  This is the jquery event instance (generated by droppable code)
 *  ui:     This is the element that was dropped (renamed for ease of use) */
function handleDropEvent(event,ui){
    var draggable = ui.draggable;

    // Revmoce default text
    //$('#infobar p').remove();
    // Add x and y divs if they don't exist
    if($('#infobar .active #xdiv').length <= 0){
        var xdiv = document.createElement('div');
        $(xdiv).addClass('span5 inputs text-left');
        $(xdiv).attr('id','xdiv');
        $(xdiv).append('X Datasets');
        $(xdiv).append('<a class="pull-right" href="javascript:void(0)" onclick="$(\'#infobar #xdiv .dataset\').remove()">Remove All <i class="icon-remove"></i></a>');
        $('#infobar .active').append(xdiv);
    }
    if($('#infobar .active #ydiv').length <= 0){
        var ydiv = document.createElement('div');
        $(ydiv).addClass('span5 inputs text-left');
        $(ydiv).attr('id','ydiv');
        $(ydiv).append('Y Datasets');
        $(ydiv).append('<a class="pull-right" href="javascript:void(0)" onclick="$(\'#infobar #ydiv .dataset\').remove()">Remove All <i class="icon-remove"></i></a>');
        $('#infobar .active').append(ydiv);
    }
    $('#infobar .active').append('<div class="row"></div>');

    if(($('#infobar #' + draggable.attr('data-type')).length > 0) && (draggable.hasClass('dim'))){return;} // Cannot add multiple x dimensions

    // Add the appropriate div and any select box for aggregation types that they need
    var info_div = document.createElement('div');
    $(info_div).addClass('dataset text-left');
    $(info_div).attr('id',draggable.attr('data-type'));
    $(info_div).attr('data-name',draggable.attr('id'));
    $(info_div).append('<a class="pull-right" href="javascript:void(0)" onclick="$(this).parent().remove()"><i class="icon-remove"></i></a>');
    $(info_div).append(beautify(draggable.attr('data-type')));

    // Put the div in the correct place
    if(draggable.hasClass('dim')){
        var level_arr = draggable.attr('data-levels').split('|');
        if(level_arr.length > 1){
            var level_select = document.createElement('select');
            $(level_select).addClass('span2 pull-right');
            $.each(level_arr,function(index,value){
                $(level_select).append($('<option />').val(value).text(value));
            });
        }
        $(info_div).append(level_select);
        $('#infobar .active #xdiv').append(info_div);
    }else if(draggable.hasClass('meas')){
        // Add the specific select options
        var measure_arr = draggable.attr('data-aggs').split('|');
        var measure_select = document.createElement('select');
        $(measure_select).addClass('span1 pull-right');
        $.each(measure_arr, function(index, value){
            $(measure_select).append($('<option />').val(value).text(value));
        });
        $(info_div).append(measure_select);
        $('#infobar .active #ydiv').append(info_div);
    }
}

/* Droppable event handler for the rough cut tool
 *
 * This handles the drop event on the rough cut tool (or the slicer).  Any dimension
 * dropped onto the slice pane or any infobar (middle box) pane other than the Dataset Selector
 * will add the title of the dimension to the active slice pane, refocus to that pane, and send out 
 * a call to the cube to grab data for the appropriate elements in each dimension
 *
 * Input Arguments:
 *  event:      This is the jquery event instance (generated by the droppable code)
 *  ui:         This is the element that was dopped (renamed for convenience)*/
function RCTDrop(event,ui){

    // If the current active pane is the Dataset selector, refer our to the hnadleDropEvent function
    // then return
    if($('#infobar .active').attr('id') == "DatasetSel"){
        handleDropEvent(event,ui);
        return;
    }

    var draggable = ui.draggable;

    // If it isn't a dimension, we can't cut on it
    if((draggable.attr('data-kind') != "dimension") && (draggable.attr('data-kind') != 'slice')){return;}

    // Shift the tab back to the Rough Cut Tool
    $('#infoTabs [href="#RCT"]').tab('show');
    $('#infobar').slideDown();
    $('#RCTName').empty();
    $('#RCTCut').empty();
    var display_text = "<h1>" + draggable.attr('data-type') + "</h1>";
    $('#RCTName').append(display_text);

    if(draggable.hasClass('range')){
        $('#RCTCut').append('<div class="span2 pull-left text-center" id="from">From</div>');
        addSelectBox('#from',draggable.attr('id'),0);
        $('#RCTCut').append('<div class="span2 pull-left text-center" id="to">To</div>');
        addSelectBox('#to',draggable.attr('id'),0);
        var display_text = '<button class="btn btn-success slice_button pull-right range" type="button" data-caller="' + draggable.attr('id') + '">';
        display_text += '<i class="icon-arrow-right pull-right"></i></button>';
        $('#RCTCut').append(display_text);
    }
    else{
        // Now that we have the title up, we fill in the drop downs
        addSelectBox('#RCTCut',draggable.attr('id'),0); 
    }
}

/* Adds the select boxes for the slicing (RCT) tool
 *
 * This function will add the appropriate select box based on a cube call.  The data will return, and 
 * based on that data it will propagate the select box with one default value (a dummy value for UI reasons)
 * and the results from that cube call
 *
 * Input Arguments:
 *  dimension:  The dimention that you are investigating (for example location or date)
 *  level:      The level of the data you wane (for example for dimension location, it would be region,country or place)
 *  value:      The value of the level you are cutting on (for example cutton on country, the value could be Angola)
 *  depth:      The depth at which you are cutting (for example in location country is depth 2 [region, COUNTRY, location])*/
function addSelectBox(target,dimension,level,value,depth){

    // If the level is not zero, than its the dimension calling
    // This is treated differently as it calls out the first level
    if( level != 0 ){
        var data = {
            "mode":level,
            "cube":$('#cube').val(),
            "dimension":dimension,
            "value":value
        }
        var cache_name = value;
    }else{
        depth = 0;
        var data = {
            "mode":"dimension",
            "cube":$('#cube').val(),
            "dimension":dimension
        }
        var cache_name = dimension;
    }
    // Check if this dimension and level are already in the local cache, if they are use them
    // otherwise call out to the cube
    if(local_cache.hasOwnProperty(cache_name)){
        processResults(target,local_cache[cache_name],depth,dimension);
    }else{
        ajax_call = $.getJSON(
            "datawarehouse/SliceBrowser",
            data,
            function(data){
                local_cache[cache_name] = data;
                processResults(target,data,depth,dimension);
            }
        );
    }
}

/* This function is responsible for building the elements that display while cutting. 
 *
 * This produces each select box, actually generates the code, and places them based on data that is
 * passed in.  This was designed to be used with the addSelectBox function.  
 *
 * Input Arguments:
 *  data:   Data to be used to propogate the select boxes.  This is usually data from the addSelectBox function
 *  depth:  Depth at which the data was called.  This is used to determine if this is the last level
 *  dimension:  Dimension for which the data was called*/
function processResults(target,data,depth,dimension){
    // We cannot aggregate and slice on the lowest level of a dimension.  To stop this
    // we will check the max-depth against the current depth (taking into account aggregation
    // varaibels)
    /*var current_depth = (($('#xdiv [data-name="' + dimension + '"]').length <= 0) ? depth :  depth + 1);
    if (current_depth >= data.max_depth){
        alert_div = document.createElement('div');
        $(alert_div).addClass('span7 alert text-center');
        $(alert_div).append('<i class="icon-warning-sign"></i>');
        $(alert_div).append(' You cannot aggregate on a dimension and slice on its lowest level at the same time');
        $('#RCTCut').append(alert_div);
        $('.alert').alert();
        return;
    }*/

    // Delete the default placeholder text if this is the first call
    if($(target + ' #'+data.meta).length <= 0){
        cut_div = document.createElement('div');
        $(cut_div).addClass('form-horizontal');
        select = document.createElement('select');
        $(select).addClass('text-right pull-left slicer')
        if(target != '#RCTCut'){
            $(cut_div).addClass('span3');
            $(select).addClass('range');
        }else{
            $(select).addClass('range');
        }
        $(select).attr('id',data.meta);
        $(select).attr('data-maxdepth',data.max_depth);
        $(select).attr('data-level',depth);
        $(select).attr('data-dim',dimension);
        button_div = document.createElement('button');
        $(button_div).addClass('text-center span1 pull-right btn btn-success slice_button');
        $(button_div).attr('type','button');
        $(button_div).attr('data-caller',data.meta);
        $(button_div).append('<i class="icon-arrow-right"></i>');
        $(cut_div).append(select);
        $(cut_div).append(button_div);
        $(cut_div).append('<br>');
        /*display_text += '<button class="text-center span1 pull-right btn btn-success slice_button" type="button" data-caller="' + data.meta + '">';
        display_text += '<i class="icon-arrow-right"></i>';
        display_text += '</button></div>';*/
        $(target + '').append(cut_div);
        if(target != '#RCTCut'){
            $(target + ' #' + data.meta).parent().children('button').remove();
        }
    }else{
        $(target + ' #' + data.meta).empty();
    }

    // Loop through the data ad append the select options
    $('#RCTDirections').text("Choose the " + data.meta + " you wish to slice on");
    $(target + ' #'+data.meta).append($("<option />").val("Default").text(data.meta));
    $.each(data.options,function(key,value){
        $(target + ' #' + data.meta).append($("<option />").val(key).text(value)); 
    });
}

/* This function moves the tutorial bar along when slicer is selected
 *
 * When the slicer tab is selected, this will change the tutorial text in the tutorial bar
 * to show help for the slice interface*/
$('#infoTabs a[href="#RCT"]').live('shown',function(ev){
    if($('#tutorial').length > 0){
        $('#tutorial').empty();
        $('#tutorial').append('<i class="icon-info-sign"></i>');
        $('#tutorial').append(' Drag and drop dimension you would like to slice on ');
        $('#tutorial').append('<a class="close" data-dismiss="alert" herf="#">&times;</a>');
    }
});

/* This is the Slice button handler
 *
 * This handles all button presses from the slice buttons found on the Slicer (Rough Cut Tool) pane
 * of the infobar (middle bar of page).  This will generate the ui elemenets that are added to the
 * slice list, as well as focus on the slice list.  This also contains the logic for whether a slice
 * is allowed to be added.  (For example, duplicate slices on dimension are not allowed at this point*/
$('.slice_button').live('click',function(){

    var level_name = $(this).attr('data-caller');
    var lvl = '#RCTCut #'+level_name;
    if($(this).hasClass('range')){
        if($('#to select').val() == 'Default' && $('#from select').val() == 'Default'){
            return;
        }
        var froms = [];
        var tos = [];
        $('#RCTCut #from select').each(function(){
            if($(this).val() != 'Default'){
                froms.push($(this).val());
            }else{
                return false;
            }
        });
        $('#RCTCut #to select').each(function(){
            if($(this).val() != 'Default'){
                tos.push($(this).val());
            }else{
                return false;;
            }
        });

        if(level_name == 'date_cubes'){
//            dimension = "Date"
            var s_fromPath = formatDate(froms)
            var s_toPath = formatDate(tos)
        }else{
            var s_fromPath = froms.join('|');
            var s_toPath = tos.join('|');
        }
        var dimension = level_name;
        var fromPath = froms.join('|');
        var toPath = tos.join('|');
        if(toPath == ''){
            var path = fromPath;
            var text_path = s_fromPath;
        }else{
            var path = fromPath + "-" + toPath;
            var text_path = s_fromPath + '-' + s_toPath;
        }
    }else{
        var depth = $(lvl).attr('data-level');
        var max_depth = $(lvl).attr('data-maxdepth');
        var dimension = $(lvl).attr('data-dim');

        if($(lvl).val() == "Default"){return;}              // If the default value is the one that was called, do nothing

        // Generates the path needed for the slice
        var path = "";
        for( var i = 0 ; i < depth ; i++){
            path += $('[data-level=' + i + ']').val() + "|";
        }
        path+=$(lvl).val();
        if((level_name == 'admin0') || (level_name == 'admin1') || (level_name == 'admin2')){
           var text_path = formatLocation(path.split('|'));
        }

    }
    // Generate html5 element that will hold the data for later processing
    var slice_div = document.createElement('div');
    $(slice_div).addClass('slice text-center');
    if($(this).hasClass('range')){$(slice_div).addClass('range');}
    $(slice_div).attr('data-dim',dimension);
    //$(slice_div).attr('id',dimension);
    $(slice_div).attr('data-path',path);
    $(slice_div).attr('data-kind','slice');
    var dim_span = document.createElement('span');
    $(dim_span).addClass('pull-left');
    $(dim_span).text(beautify(dimension) + ':');
    $(slice_div).append(dim_span);
    $(slice_div).append(text_path);
    $(slice_div).append('<a href="javascript:void(0)" onclick="$(this).parent().remove()"><i class="pull-right icon-remove"></i></a>');
    $(slice_div).append('<a href="javascript:void(0)" onclick="editSlice($(this).parent())"><i class="pull-right icon-edit"></i>');
    /*var display_text = '<div class="slice text-center" data-dim="' + dimension;
    display_text += '" data-path="' + path + '">';
    display_text += dimension + ' > ' + path;
    display_text += '<a href="javascript:void(0)" onclick="$(this).parent().remove()"><i class="pull-right icon-remove"></i></a>';
    display_text += '<a href="javascript:void(0)" onclick="editSlice($(this).parent())"><i class="pull-right icon-edit"></i>';
    display_text += '</div>';*/

    if($('#Slice_list .slice').length <= 0){$('#Slice_list .slice').remove();}
    if($('#Slice_list #' + dimension).length >= 0){
        $('#Slice_list #' + dimension).remove();
    }
    $('#infoTabs [href="#Slice_tab"]').tab('show');
    $('#Slice_list').append(slice_div).fadeIn(400);
});

/* This is the handler for the select boxes on the slice (or Rough Cut Tool) pane
 *
 * This will make the initial call when a select bpx contents' change on the 
 * Rought Cut Tool (or slice) pane in the infobar (middle pane on page).*/
$('.slicer').live('change',function(){
    var value=$(this).val();
    var cur_depth = $(this).attr('data-level');
    cur_depth++; // Corrects for indexing error
    var max_depth = $(this).attr('data-maxdepth');
    var dimension = $(this).attr('data-dim');

    // No need to call out for data if we are at the bottom of a choice tree
    if(cur_depth >= max_depth){return;}
    if(value == "Default"){return;}

    // We should delete all levels lower than the one that changed and the one that is going to be changed
    var holder = $(this).parent().parent().attr('id')
    for(var i = cur_depth; i < max_depth; i++){
        if ($('#' + holder + ' .slicer[data-level="' + i + '"]').length > 0){
            $('#' + holder + ' .slicer[data-level="' + i + '"]').parent().remove();
        }
    }

    var target = '#' + $(this).parent().parent().attr('id');
    
    addSelectBox(target,dimension,$(this).attr('id'),value,cur_depth);
});

/* This is the handler for the "Graph" button
 *
 * This will call functions to sanitize and create the outgoing data object for use
 * with the backend.  It will the call out for that data and process it once it returns
 * based on whether the user has requested a graph or a table.  
 *
 * It will create a new graph or table for every x dimension given.  It will only include
 * the y measures that were selected.  The data will only be for those slices made.
 *
 * It will then call a function to create an information block that will save the state of the
 * data browsing in case the user needs this later.
 *
 * This will also cache the data, as well as chart objects locally so fewer calls out need to 
 * be made. */
function create_output(type){
    // First we make sure selections were made
    var out_data = prepare_out_data();
    if (out_data == -1) { return; } // There was an error in preapre_out_data
    // Not that we are sure we have some dimensions to fetch, we clear out all ajax calls
    ajax_call.abort();
    // If selections were made properly, we show the visualizer and graph
    $('#visualizer').show();
    $('#graph_tools').show();
    ajax_call = $.getJSON(
                "/datawarehouse/results",
                out_data,
                function(data,textStatus){
                    $('#warning_box').empty();
                    warning = document.createElement('div');
                    if(textStatus == "success"){
                        $(warning).addClass('alert-success text-center span5 alert');
                        $(warning).append('<i class="icon-ok-sign"></i>');
                        $(warning).append(" Retrieved Data");
                    }else{
                        $(warning).addClass('alert-error text-center span5 alert');
                        $(warning).append('<i class="icon-excalamation-sign"></i>');
                        $(warning).append(' An Unknown Error Occurred');
                    }
                    $('#warning_box').append(warning);
                    window.result_object = data; // Store the returned aggregation data dictionary
                    // Parse out the data into the appropriate measures
                    //
                    var tag = $('#graph_holder .active').attr('id');
                    $('#' + tag).empty();
                    $('#data_error_box').empty();
                    charts[tag]  = {};
                    var rec_tables = [];
                    var unique_slices = [];
                    var yData = [];
                    var xData = [];
                    var has_data = true;

                    // Determind the suffixes for measures


                    // Cycle through each x dimensions that is returned.  This is kept
                    // as an outer "shell" for the measure data
                    $.each(data,function(key,value){
                        if(key == "slices"){return true;}

                        // Check to make sure this has data, if not move on
                        var length = 0;
                        for(var count in value) length++;
                        if(length <= 1){return true;}

                        // Grab distinct slices
                        unique_slices = data.slices.filter(function(itm,i,a){return i == a.indexOf(itm)});

                        // Determine the slice suffix
                        if (unique_slices.length==1 && unique_slices[0]==""){
                            suffix="";
                        }else{
                            $.each(value,function(k,v){
                               if(k.indexOf(value['level']) == 0){
                                   suffix = k.substr(value['level'].length)
                               }
                            });
                        }

                        // Grab all the y data needed for the graph or table
                        yData = measure_array(value,suffix);

                        // Get the xData
                        // Since all slices have same xdata, should be fine with any slice
                        $.each(value,function(k,v){
                            if(k.indexOf(value['level']) == 0){
                                // Check if the array we should be using is only nulls
                                if(v.filter(function(itm, i, a){return i == a.indexOf(itm);})[0] == null){
                                    text = document.createElement('p');
                                    $(text).addClass('alert alert-error text-center');
                                    $(text).append('<i class="icon-warning-sign"></i>');
                                    $(text).append('No Data was returned for ' + value['level']);
                                    $('#data_error_box').append(text);
                                    has_data = false;
                                    return false;
                                }
                                xData = v;
                                return false;
                            }
                        });
                        if(!has_data){
                            // There is no xData for this graph, we move on
                            return true;
                        }
                        //xData = value[value['level'] + unique_slices[0]];
                        if(xData == undefined){
                            text = document.createElement('p');
                            $(text).addClass('text-error text-center');
                            $(text).append('<i class="icon-warning-sign"></i>');
                            $(text).append('No Data was returned for ' + value['level'] + unique_slices[0]);
                            $('#data_error_box').append(text);
                            return true;
                        }

                        // Create a place to show the graph or table
                        $($('#graph_holder .active')[0]).append('<div class="chart" id="' + key + '"></div>');
                        var element = $('#graph_holder .active #' + key);
                        if (type == 'graph'){
                            var chart_obj = parseDataToChart(element,value,xData,yData);
                            charts[tag][$(element).attr('id')] = new Highcharts.Chart(chart_obj)
                            $('#tabList a[href="#' + tag + '"]').trigger('shown');
                        }else if(type =='table'){
                            create_table(element,value,xData,yData);
                        }else{
                            warning = document.creatElement('div')
                            $(warning).addClass('text-error alert-error span5 alert text-center');
                            $(warning).append('<i class="icon-exclamation-sign"></i>');
                            $(warning).append('An Unexpected Error has Occurred');
                            $('warning_box').append(warning);
                            $('.alert').alert();
                            return;
                        }

                        // Build the record table for the info box
                        var sum_records = 0;
                        $.each(unique_slices,function(i,slice_val){
                            try{
                                $.each(value['record_count' + slice_val],function(index,val){
                                    sum_records += val;
                                });
                                table = document.createElement('table');
                                $(table).append('<tr><th> ' + value['level'] + slice_val + ' </th><th> Records Used </th></tr>');
                                for(var i = 0; i < value[value['level'] + slice_val].length; i++){
                                    var table_text = '<tr><td>';
                                    table_text += value[value['level'] + slice_val][i] + '</td><td>';
                                    table_text += value['record_count' + slice_val][i] + '</td></tr>';
                                    $(table).append(table_text);
                            }
                            }catch(TypeError){
                            }
                            $(table).append('<tr><th> Total: </th><td>' + sum_records + '</td></tr>');
                            rec_tables.push(table);
                        });
                    });
                    local_cache[tag] = window.result_object;

                    create_info_block(rec_tables,out_data);
                }
            )
            .fail(function() {
                warning = document.createElement('div');
                $(warning).addClass('alert span5 text-error text-center');
                $(warning).append('<i class="icon-warning-sign"></i>');
                $(warning).append(' An Unknown Server Error Occured');
                $('#warning_box').append(warning);
                $('.alert').alert();
            });
//});
}

/* This function parses the returned data from the cube into a Highchart object
 *
 * This will also filter the y and x data so that only those datasets are shows*/
function parseDataToChart(element,data,xData,yData){
    var xTitle = "";
    var Title = data['level'];

    //yData = measure_array(data);
     /*for (key in data) {             // Parse the returned data into x and y
        if (data.hasOwnProperty(key)) {
            if (key == xAxis){
                xData = data[key];
                xTitle = key;
            }
            else if (key != 'level'){
                yData.push({name: key, data: data[key]});
            }
        }
    }*/

    // Grab the active pane element for graphing
    var chart_obj = getChart(element,'line', Title, xData, xTitle, yData, '');
    return chart_obj;
}

// Slice removal function
function removeSlice(dimension){
    $('#Slice_list #'+dimension).remove();
} 
// Edit the slice
function editSlice(dim_chunk){
    //var dim_chunk = $(dimension)
    //var dim_chunk = $('#dimensions #' + dimension);
    var dimension = $(dim_chunk).attr('data-dim');
    var dataLabel = $('#dimensions #' + $(dim_chunk).attr('data-dim')).text();
    $('#infoTabs [href="#RCT"]').tab('show');

    // Empty the name and cut boxes
    $('#RCTCut').empty();

    var path = $(dim_chunk).attr('data-path')

    if($(dim_chunk).hasClass('range')){
        var dim = $('#dimensions [id="' + dim_chunk.attr('data-dim') + '"]')
        sliceDrop(
            ev = {target:$('#Slice_list')},
            ui = {draggable:dim}
        );
        var toPath = path.split('-')[1];
        var fromPath = path.split('-')[0];
        var to_arr = toPath.split('|');
        var from_arr = fromPath.split('|');
        for (var i = 0; i < to_arr.length; i++){
            var select_box = $($('#RCT #to select')[i]);
            select_box.val(to_arr[i]);
            select_box.trigger('change');
        }
        for (var i = 0; i < from_arr.length; i++){
            var select_box = $($('#RCT #from select')[i]);
            select_box.val(from_arr[i]);
            select_box.trigger('change');
        }
    }else{
        addSelectBox('#RCTCut',$(dim_chunk).attr('data-dim'),0);
        var path_arr = path.split('|');

        // Loop through the path and fill out the select boxes   
        for (var i = 0; i < path_arr.length; i++){
            var select_box = $($('#RCTCut select')[i]);
            select_box.val(path_arr[i]);
            select_box.trigger('change');
        }
        $('#sliceModal').modal();
    }
    $(dim_chunk).remove();
//    $('#RCTName').empty();
//    var display_text = "<h1>" + dataLabel + "</h1>";
//    $('#RCTName').append(display_text);
}

/* This function adds a "window" to the graphing pane */
function addPane(){
    var paneNum = $('#visualizer .tab-pane').length + 1
    var display_text = '<li><a href="#pane' + paneNum + '" data-toggle="tab">Window ' + paneNum + '</li>';
    $('#tabList').append(display_text);
    var display_text = '<div class="tab-pane graph-pane" id="pane' + paneNum + '"></div>';
    $('#graph_holder').append(display_text);
    $('#tabList [href="#pane' + paneNum + '"]').tab('show');
}

// Removes active pane
function removePane(){
    $('#graph_holder .active').remove();
    $('#tabList .active').remove();
    $('#tabList a:first').tab('show');
}

$('#load_box').on({
    ajaxStart:function(){
        $('#build_dataset').hide();
        $(this).addClass('loading');
    },
    ajaxStop:function(){
        $(this).removeClass('loading');
        $('#build_dataset').show();
    }
});

/* This function restores the slices and datasets to the infobar
 *
 * This function will examine the datasets and slices in the information section
 * at the bottom of a graph.  It will then restore these to the info bar area (allowing
 * for modification of the original graphs datastructure).  This will also reset the cube
 * to the cube that was used to generate the graph.*/
function restoreState(){
    var ui=[];

    // Select the correct cube
    $('#cube').val($('#graph_holder .active #ds_cube').attr('data-cube-name'));
    $('#cube').triggerHandler('change');

    // Replace x and y datasets
    $('#infocontrol [href="#DatasetSel"]').tab('show');
    $('#graph_holder .active #info_xdiv .dim').each(function(){
        ui['draggable'] = $(this);
        handleDropEvent('dummy',ui);
    });
    $('#graph_holder .active #info_ydiv .meas').each(function(){
        ui['draggable'] = $(this);
        handleDropEvent('dummy',ui);
    });
    $('#infocontrol [href="#RCT"]').tab('show');
    $('#graph_holder .active #info_slice .slice').each(function(){
        var $copy = $(this).clone();
        $copy.removeClass('span10');
        //$copy.addClass('span7 offset2');
        var append_text = '<a href="javascript:void(0)" onclick="removeSlice(' + "'" + $copy.attr('id') + "'" +')"><i class="pull-right icon-remove"></i></a>';
        append_text += '<a href="javascript:void(0)" onclick="editSlice(' + "'" + $copy.attr('id') + "'" + ')"><i class="pull-right icon-edit"></i></a>';
        $copy.append(append_text);
        $('#Slice_list').append($copy);
    });
}

/* This function prepares the outgoing data from the datasets selected
 *
 * This function will parse through the slice and dataset lists and create 
 * a single object to be submitted to the backend. 
 *
 * Output Parameter:
 *  out_data =  This will contain all of the out_data information needed for a 
 *              server call.*/
function prepare_out_data(){
    // Clear the warning ox
    $('#warning_box').empty();

    // Check for problems
    var warning_text = '';
    if($('#xdiv .dataset').length <= 0){
        warning_text += "No x dimension was chosen, please choose a x dimension\n";
    }
    if($('#ydiv .dataset').length <= 0){
        warning_text += "No y dimension was chosen, please choose a y dimension\n";
    }

    var u_slice = unique_attribute($("#Slice_list .slice"), "data-dim");
    if(u_slice){
        warning_text += "Only one slice is allowed per dimension.  Multiple Slices have been chosen for the ";
        warning_text += beautify(u_slice) + " dimension\n";
    }
    // If there are warnings, tell the user and return
    if(warning_text != ''){alert(warning_text); return -1;}

    // Setup outgoing JSON data
    var out_data = {"num_slices":$('#Slice_list .slice').length,"cube":$('#cube').val()};
    out_data['num_measures'] = $('#ydiv .dataset').length;
    // Process the slice list
    $('#Slice_list .slice').each(function(index){
        out_data["dimension_" + index] = $(this).attr('data-dim');
        out_data["path_" + index] = $(this).attr('data-path');
    });
    // Process the measures for the y datasets
    /*$('#ydiv .dataset').each(function(index){
        out_data["measure_"+index] = $(this).attr('data-name') + '_' + $(this).find('select').val();
    });*/
    // Process the dimensions for x (only allowing one for now)
    var drillArray = [];
    var drillPaths = [];
    $('#xdiv .dataset').each(function(){
        drillArray.push($(this).attr('data-name'));
        drillPaths.push($(this).children('select').val());
        //if($(this).children('select').length > 0){drillPaths.push($(this).children('select').val());}
    });
    out_data["drilldim"] = drillArray.join("|");
    out_data['drillpath'] = drillPaths.join("|");
    out_data["interface"] = "native";
    return out_data;
}

/* This will determine of the given list of DOM elements are unique given an attribute to search on
 *
 * This takes a list of DOM elements (a jQuery selector) and an attribute string and searched each
 * DOM element for that string.  If it finds one that is not null, it will then add it to a list.
 * Once a non-unique element is found, it will return the value of the dimension that it found to
 * be non-unique.  If it does not find one, it will return false.
 *
 * Input Parameters:
 *  domList = List of DOM elements (jQuery selector)
 *  attr    = String of attribute to search uniquness for
 */
function unique_attribute(domList, attr){
    var attrs = [];
    var retval = false;
    $.each(domList, function(index, value){
       if($.inArray($(value).attr(attr), attrs) != -1){
           retval = $(value).attr(attr);
       }else {
           attrs.push($(value).attr(attr))
       }
    });
    return retval;
}

/* This function creates the information area at the bottom of the graphs
 *
 * This will take data from the current selections and put them into an area at the
 * bottom of a graph or table.  This is done so that the state for that particular
 * graph or table is saved and can be restored.
 *
 * This will autoamtically target the active graphing window.
 *
 * Input Parameters:
 *  rec_tables =    A list containing DOM element tables 
 *  out_data =      The output object used to fetch the data (This is used to
 *                  create the query string)*/
function create_info_block(rec_tables,out_data){
    // If the graph_info div already exists, it is outdated, so destroy it
    $('#graph_holder .active #graph_info').remove();

    // Create the graph_info div
    var new_div = document.createElement('div');
    $(new_div).addClass('text-center graph-info');
    $(new_div).attr('id','graph_info');
    //$('#graph_holder .active').append('<div class="row"></div>');
    $('#graph_holder .active').append(new_div);
    // Add the name tags (dataset selection and table titles)
    /*dataset_title = document.createElement('div');
    $(dataset_title).attr('id','data_summary_tag');
    $(dataset_title).append('<h3>Dataset Selection Summary</h3>');
    $(new_div).append(dataset_title);
    dataset_title = document.createElement('div');
    $(dataset_title).attr('id','count_table_tag');
    $(dataset_title).append('<h3>Displayed Data</h3>');
    $(new_div).append(dataset_title);
    $(new_div).append('<br>');*/
    // Add the dataset information panel (left half)
    var ds_div = document.createElement('div');
    $(ds_div).append('<div id="data_summary_tag"><h3>Dataset Selection Summary</h3></div>');
    var datasets = document.createElement('div');
    $(datasets).addClass('pull-left dataset_info');
    $(ds_div).attr('id','data_summary');

    var info_holder = document.createElement('div');
    $(info_holder).attr('id','info_holder');
    $('#graph_holder .active #graph_info').append(info_holder);
    $(info_holder).append(ds_div);
    // Add cube information
    var cube_div = document.createElement('div');
    $(cube_div).addClass('ds_cube');
    $(cube_div).attr('id','ds_cube').attr('data-cube-name',$('#cube').val());
    name_div = document.createElement('div')
    $(name_div).addClass('dataset_name');
    $(name_div).append('Cube')
    $(cube_div).append(name_div)
    //$(cube_div).append('<p>Cube</p>');
    var cube_data = document.createElement('div');
    var cube_name = $('#cube option[value="' + $('#cube').val() + '"]').text();
    $(cube_data).addClass('dataset_data');
    $(cube_data).append(cube_name);
    $(cube_div).append(cube_data);
    $(datasets).append(cube_div);
    // Add Slices
    slice_info_div = document.createElement('div');
    $(slice_info_div).addClass('inputs');
    $(slice_info_div).attr('id','info_slice');
    $(slice_info_div).text('<p>Slices</p>');
    slice_list = []; // This will be used for file downloads
    $('#Slice_list .slice').each(function(){
        var $slice_clone = $(this).clone();
        $slice_clone.children('a').remove();
        $(slice_info_div).append($slice_clone);
        slice_obj = {dimension: $slice_clone.attr('data-dim'),path: $slice_clone.attr('data-path')}
        slice_list.push(slice_obj);
    });
    //$(datasets).append(slice_info_div);
    // Add X and Y information divs
    var info_xdiv = document.createElement('div');
    $(info_xdiv).attr('id','info_xdiv');
    x_name_div = document.createElement('div');
    $(x_name_div).addClass('dataset_name');
    $(x_name_div).append('X Dimensions');
    $(info_xdiv).append(x_name_div);
    var info_ydiv = document.createElement('div');
    $(info_ydiv).attr('id','info_ydiv');
    y_name_div = document.createElement('div');
    $(y_name_div).addClass('dataset_name');
    $(y_name_div).append('Y Measures');
    $(info_ydiv).append(y_name_div);
    $(datasets).append(info_xdiv);
    $(datasets).append(info_ydiv);
    $(ds_div).append(datasets);
    // Fill those divs
    x_data_div = document.createElement('div');
    $(x_data_div).addClass('dataset_data');
    dims = []; // This will be used for file downloads
    $('#xdiv .dataset').each(function(){
        var $clone = $($('#dimensions #' + $(this).attr('data-name'))[0]).clone()
        $clone.children('a').remove();
        //$clone.removeClass('dim')
        $(x_data_div).append($clone);
        obj = {
            'id':$clone.attr('id'),
            'data-levels':$clone.attr('data-levels'),
            'select-val': $(this).children('select').val()
        }
        dims.push(obj);
    });
    $(info_xdiv).append(x_data_div);
    y_data_div = document.createElement('div');
    $(y_data_div).addClass('dataset_data');
    meas_list = []; // This will be used for file downloads
    $('#ydiv .dataset').each(function(){
        var $clone = $($('#measures #' + $(this).attr('data-name'))[0]).clone();
        $clone.children('a').remove();
        var text = $clone.text();
        text += ' ' + $(this).children('select').val();
        $clone.text(text);
        //$clone.removeClass('meas')
        $(y_data_div).append($clone);
        obj = {
            'id':$clone.attr('id'),
            'data-aggs': $clone.attr('data-aggs'),
            'select-val': $(this).children('select').val()
        }
        meas_list.push(obj);
    });
    $(info_ydiv).append(y_data_div);
    // The counts tables
    var table_div = document.createElement('div');
    $(table_div).attr('id','count_table');
    var tables = document.createElement('div');
    $(tables).addClass('dataset_info pull-right text-center');
    $.each(rec_tables,function(index,val){
        $(tables).append(val);
        $(tables).append('<br>');
    });
    $(table_div).append(tables);
    $(table_div).prepend('<div id="count_table_tag"><h3>Displayed Data</h3></div>')
    // Add tables
    $(info_holder).append(table_div);
    var restore_button = document.createElement('div');
    $(restore_button).attr('id','info_controls');
    $(restore_button).append('<a class="btn info_button" href="javascript:void(0)" onclick="restoreState()" data-toggle="tooltip" title="Restore datasets and slices of this graph to the infobar" id="restore_button">Restore</a>');
    dlform = document.createElement('form');
    $(dlform).attr('id','dlform');
    $(dlform).attr('action','dlform');
    $(dlform).attr('method','post');
    $(dlform).attr('target','_blank')
    $(dlform).append(csrf_tag);
    $(dlform).append('<input type="hidden" id="file_name" name="file_name">');
    $(dlform).append('<input type="hidden" id="content" name="content">');
    $(dlform).append('<input type="submit" class="info_button btn" value="Save">');
    $(restore_button).append(dlform);
    var query_alert = document.createElement('div');
    $(query_alert).addClass('alert alert-info text-center');
    $(query_alert).attr('id','query_string');
    $(query_alert).append(location.protocol + '//' + location.host + '/datawarehouse/results/?' + decodeURIComponent($.param(out_data)));
    $('#graph_holder .active #graph_info').append(restore_button);
    $('#graph_holder .active #graph_info').append(query_alert);
    $('.alert').alert();

    // Now we form the JSON object that will be used to save this layout if the "save" button
    // is clicked
    file_name="Datawarehouse.json"
    content = {
        cube: $('#cube').val(),
        dimensions: dims,
        measures: meas_list,
        slices: slice_list
    };
    $('#graph_holder .active #dlform #file_name').val(file_name);
    $('#graph_holder .active #dlform #content').val(JSON.stringify(content));
}

/* This function will create a data table
 *
 * This function takes data from the server and instead of creating
 * a graph it creates a table.  Once the table is created and placed
 * it is converted into a Datatable for user friendly and export 
 * functionality.
 *
 * This will place only measures selected at the Dataset Selector into 
 * the table
 *
 * Input Arguments:
 *  element =   The DOM element that the table will be placed in
 *  data    =   The data to be used to create the table*/
function create_table(element,data,xData,yData){
    var xTitle = '';

    //yData = measure_array(data);
    
    table = document.createElement('table');

    // Create table headers
    var dim = data['level'].split('.')[0];
    var raw_levels = $('#dimensions #' + dim).attr('data-levels').split('|') ;
    var levels_arr = [];
    $.each(raw_levels,function(index,value){
        levels_arr.push(value);
        var data_name = dim + '.' + value;
        if(data_name == data['level']){return false;}
    });
    var table_text = '<thead><tr>';
    $.each(levels_arr,function(index, value){
        var data_name = ((raw_levels.length == 1) ? value : dim + '.' + value);
        table_text += '<th> ' + beautify(data_name) + ' </th>';
    });
    $.each(yData,function(index, value){
        table_text += '<th> ' + value.name + '</th>';
    })
    table_text += '</tr></thead>';
    $(table).append(table_text);
    $(table).append('<tbody>');

    for(var i = 0; i < xData.length ; i ++){
        table_text = '<tr>';
        $.each(levels_arr,function(index,value){
            var data_name = ((raw_levels.length == 1) ? value : dim + '.' + value);
            try{
                table_text += '<th> ' + data[data_name][i] + ' </th>';

            } catch (TypeError) {
                table_text += '<th> ' +xData[i] + ' </th>';
            };
        });
        $.each(yData,function(index,value){
            table_text += '<td>' + value.data[i] + '</td>';
        });
        table_text += '</tr>';
        $(table).append(table_text);
    }
    $(table).append('</tbody>');
    $(element).append(table)
    $(element).children('table').dataTable({
        "sDom": 'T<"clear">lfrtip',
        "oTableTools": {
	        "sSwfPath": "/static/datawarehouse/TableTools/media/swf/copy_csv_xls_pdf.swf",
            "aButtons": [
                "copy",
                {
                    "sExtends": "xls",
                    "sTitle": "vecnetDataWarehouse",
                    "sButtonClass": "btn"
                },
                {
                    "sExtends": "pdf",
                    "sTitle": "vecnetDataWarehouse"
                },
                "print"
            ]
         }
    });

}

/* This function will return an array containing the measures selected
 *
 * Input Arguments:
 *  data =      The data returned from the server
 * Output Values:
 *  yData =     This is an array of dictionaries containing the name and data 
 *              for each given measure.*/
function measure_array(data,suffix){
    var yData = new Array();

    $('#ydiv .dataset').each(function(index){
        var data_type = $($('#ydiv .dataset')[index]).children('select').val();
        var data_name = $(this).attr('data-name') + "_" + data_type + suffix;
        if(data[data_name] == undefined){
            text = document.createElement('p');
            $(text).addClass('alert alert-error text-center');
            $(text).append('<i class="icon-warning-sign"></i>');
            $(text).append('No Data was returned for ' + data_name);
            $('#data_error_box').append(text);

        }else{
            yData.push({name:beautify(data_name), data: data[data_name]});
        }
    });

    return yData;
}

function dataSort(xData,yData){

    xData_copy = xData.slice(0);
    xData_copy.sort(function(a,b){return a-b});

    new_yData = {};

    $.each(yData,function(key,index){
        for( var i = 0; i < xDim_copy.length; i++){
            data = $this.data.slice(0);
            new_data = [];
            new_data[i] = data[xData.indexOf(xData_copy[i])];
            new_yData.push({name:$this.name,data: new_data});
        }
    });

    return;
}

/* This function will change options for Highcharts chart
 *
 * When given the object within a chart object that needs to be changed,
 * the options that needs to be changed, and the option to change it to,
 * this will redraw a Highcharts chart.
 *
 * Input Parameters:
 *  obj = The object (ex legend, chart, etc)
 *  options = The option to change (ex float, background-color)
 *  style = The new value of the option (this supports "toggle" for on/off
 *          options)
 */
function changeOption(obj,option,style){
    var element = $($('#graph_holder .active')[0]).attr('id');
    if (charts[element] == undefined){return;}        // CHeck for charts existence
    if(obj == 'chart'){selector = '#window_graph_chooser';}
    if(obj == 'legend'){selector = '#legend_graph_chooser';}
    key = $(selector).val();
    if(key == 'Default'){return;}
    chart = charts[element][key];
    var chart_data = chart.options;
    if(style == "toggle"){
        style = !chart_data[obj][option]
    }
    chart.destroy();                        // Destroy current chart to build new one
    if(obj == 'xAxis' || obj == 'yAxis'){
        chart_data[obj][0][option] = style;
    }else{
        chart_data[obj][option] = style;
    }
    var new_chart = new Highcharts.Chart(chart_data);
    charts[element][key] = new_chart;
}


/* This is the handler for the axis type select
 *
 * When the Axis type is changed, this will handle the "change"
 * event from the select box.  This will then use changeOption and
 * change the appropriate axis type.
 */
$('#window_opts .type-sel').on('change',function(){
    changeOption($(this).attr('data-axis'),'type',$(this).val());
});

/* The following are colorpicker handlers
 *
 * The bootstrap colorpicker fires a "changeColor" event
 * every time the colorpicker button is pressed and a new
 * color is chosen.  This handles all of the colorpicker
 * buttons, and their "changeColor" event.
 *
 * These will then use the changeOption function to change the
 * appropriate color.
 */
$('#windowbg-cp').colorpicker().on('changeColor',function(ev){
    changeOption('chart','backgroundColor',ev.color.toHex());
});
$('#windowbrdr-cp').colorpicker().on('changeColor',function(ev){
    changeOption('chart','borderColor',ev.color.toHex());
});
$('#plotbg-cp').colorpicker().on('changeColor',function(ev){
    changeOption('chart','plotBackgroundColor',ev.color.toHex());
});
$('#plotbrdr-cp').colorpicker().on('changeColor',function(ev){
    changeOption('chart','plotBorderColor',ev.color.toHex());
});
$('#legendbg-cp').colorpicker().on('changeColor',function(ev){
    changeOption('legend','backgroundColor',ev.color.toHex());
});
$('#legendbrdr-cp').colorpicker().on('changeColor',function(ev){
    changeOption('legend','borderColor',ev.color.toHex());
});

/* This handler is responsible for changing the color of the associated series
 *
 * Upon selection of a series, the colorpicker button will change the color of
 * the selected series in the selected graph.
 */
$('#series-cp').colorpicker().on('changeColor', function(ev){
    var element = $($('#graph_holder .active')[0]).attr('id');
    var chart_name = $('#window_graph_chooser').val();
    if (chart_name == 'Default'){return;}        // CHeck for correct settings in chart chooser
    var chart = charts[element][chart_name];
    var chart_data = chart.options;
    var series_ndx =
    chart.destroy();
    chart_data.colors[$('#series-colors').val()] = ev.color.toHex();
    var new_chart = new Highcharts.Chart(chart_data);
    charts[element][chart_name] = new_chart;
});

/* This is the text controls for each graph
 *
 * This is a handler for the form on the title tab of the
 * Highcharts toolbar.  This will change the title values
 * for the selected graph.  This is fired when the "Change Text"
 * button is clicked.
 *
 * This actually uses a form, but changes the default action so that
 * it is not actually submitted.
 *
 * This calls the changeText function to actually change the text
 */
$('#text_change_form').on('submit',function(ev){
    ev.preventDefault();
    var element = $('#graph_holder .active').attr('id');
    var chart_name = ev.target.text_graph_chooser.value;
    if(chart_name == 'Default'){return false;}
    chart = charts[element][chart_name];
    if(ev.target.graph_title.value != ''){chart.setTitle({ text: ev.target.graph_title.value });}
    if(ev.target.graph_subtitle.value != ''){chart.setTitle(null,{ text: ev.target.graph_subtitle.value });}
    if(ev.target.graph_xtitle.value != ''){chart.xAxis[0].setTitle({ text: ev.target.graph_xtitle.value })}
    if(ev.target.graph_ytitle.value != ''){chart.yAxis[0].setTitle({ text: ev.target.graph_ytitle.value })}
    return false;
});

/* This function changes the text for a given Highchart Chart
 *
 * This will, given the title type, read the information from the
 * title page on the highcharts toolbar, and change that title type.
 *
 * This was originally used with the "quick change" title changer,
 * but was deprecated after Kristina's new design.
 */
function changeText(title_type){
    var element = $('#graph_holder .active').attr('id');
    var chart_name = $('#quick-text-change').val();
    var text_val = $('#graph_text').val();
    if(chart_name == 'Default'){return;}
    chart = charts[element][chart_name];
    switch(title_type){
        case 'title': chart.setTitle({ text: text_val }); break;
        case 'subtitle': chart.setTitle(null, { text: text_val }); break;
        case 'xAxis': chart.xAxis[0].setTitle({ text: text_val }); break;
        case 'yAxis': chart.yAxis[0].setTitle({ text: text_val }); break;
        default:return
    }

}

/* This is the tab handler for the visualizer tabs
 *
 * When a tab is changed, different elements of the DW Browser also
 * have to change.  These changes are triggered off of the "shown"
 * event type from the tabs.
 *
 * Some things that are changed are the graph options for the HighCharts
 * toolbar as well as the restore functionality.
 */
$('#tabList a').live('shown',function(ev){
    var target = $(this).attr('href');
    var chart = charts[target.split('#')[1]]

    // Enable or disable buttons based on the presence of a chart
    if(chart == undefined){
        $('#HighChart_toolbar a').each(function(){
            $(this).attr('disabled','disbaled');
        });
        $('#HighChart_toolbar button').each(function(){
            $(this).attr('disabled','disbaled');
        });
        $('#HighChart_toolbar select').each(function(){
            $(this).attr('disabled','disabled');
        });
        return;
    }else{
        $('#HighChart_toolbar a').each(function(){
            $(this).removeAttr('disabled');
        });
        $('#HighChart_toolbar button').each(function(){
            $(this).removeAttr('disabled');
        });
        $('#HighChart_toolbar select').each(function(){
            $(this).removeAttr('disabled');
        });
    }

    // Update the choices for the graph selectors
    var selectors = ['#text_graph_chooser','#window_graph_chooser','#legend_graph_chooser'];
    $.each(selectors,function(i,val){
        $(val).empty();
        $(val).append($('<option />').val('Default').text('Please select a graph'));
    });
    $('#quick-text-change').empty();
    $('#quick-text-change').append($('<option />').val('Default').text('Please select a graph'));
    $('#quick-series-graph').empty();
    $('#quick-series-graph').append($('<option />').val('Default').text('Please select a graph'));
    $.each(chart,function(key,value){
        $.each(selectors,function(i,val){
            $(val).append($('<option />').val(key).text(value['title'].text));
        })
        $('#quick-text-change').append($('<option />').val(key).text(value['title'].text));
        $('#quick-series-graph').append($('<option />').val(key).text(value['title'].text));
    });

    // If there is a chart, fill the select box with colors
    /*$.each(chart.options.colors,function(index,value){
        $('#series-colors').append($('<option />').val(index).text(index));
    });*/
});


/* This is the handler responsible for filling the series colorpicker with options
 *
 * Upon selection of a graph on the graph tab of the highcharts toolbar, this function
 * will fill the in the options for the series list in the chart object.  This allows
 * for the changing of colors for specific series in specific graphs
 */
$('#window_graph_chooser').on('change',function(){
    if($(this).val() == 'Default'){return;}
    var element = $('#graph_holder .active').attr('id');
    var chart_name = $(this).val();
    var chart = charts[element][chart_name];
    $('#series-colors').empty();
    $.each(chart.series,function(index,value){
        $('#series-colors').append($('<option />').val(index).text(value.name));
    });
});

function clearAll(){
    // First we abort any ajax calls still pending
    ajax_call.abort();

    //Now we clear everything out
    $('#cube').val('Default');
    $('#dimensions .dim').remove();     // Remove all dimensions
    $('#measures .meas').remove();      // Remove all measures
    $('#Slice_list .slice').remove();   // Remove all slices
    $('#xdiv .dataset').remove();       // Remove all dimensions in xdiv
    $('#ydiv .dataset').remove();       // Remove all measures in ydiv
    $('#visualizer').hide();
    $('#graph_tools').hide();           // Re-hide the
    $('#graph_holder .active').empty(); // Empty the graph holder tab that is active
    $('#graph_info').empty();           // Clear the information area below the graph
}


//function addAll(){
//    if ($('#infoTabs .active a').attr('href') == '#RCT'){
//        return;
//    }
//    else{
//        $('#dimensions .dim').each(function(){RCTDrop('dummy',ui = {draggable:$(this)})});
//    }
//}

function formatDate(date_list){
    var months = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

    if(date_list.length == 1){
        return date_list[0]
    }else if(date_list.length == 2){
        return months[parseInt(date_list[1]) - 1] + ' ' + date_list[0]
    }else if(date_list.length == 3){
        return months[parseInt(date_list[1]) - 1] + ' ' +date_list[2] + ', ' + date_list[0]
    }
}

function formatLocation(loc_list){
    if(loc_list.length == 1){
        return loc_list[0];
    }else if(loc_list.length == 2){
        return loc_list[1] + ' ' + loc_list[0];
    }else if(loc_list.length == 3){
        return loc_list[2] + ', ' + loc_list[1] + ' ' + loc_list[0]
    }
}