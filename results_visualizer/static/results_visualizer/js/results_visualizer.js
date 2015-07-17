/**
 * Created with PyCharm.
 * User: creinkin
 * Date: 1/9/14
 * Time: 1:20 PM
 * To change this template use File | Settings | File Templates.
*/

    // this function escapes all non-jquery characters. This only needs to be done on the lookup side.
    // html elements will still contain these characters in their ids, but when they are being referenced, escaping
    // is necessary to query the element.
    function jQuerySelectorEscape(expression)
    {
        return expression.replace(/[!"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, '\\$&');
    }

    var seriesCount = 1; // used to increment the series number as they are added to the chart
    var currentXHR; // keeps track of the current series request to the server so it can be manually aborted
    // this will be needed for eventually getting a csv download from the server
    // var seriesList = [];

    // add a default stockchart to the page as a placeholder
    var chart = new Highcharts.StockChart(
    {
        chart:
        {
            renderTo: 'highchart-placeholder',
            spacingLeft: 60,
            height: 500
        },
        title:
        {
            text: " " //setting the title text to a space character keeps the chart from overlapping with the
                      // menu button in the upper corner.
        },
        rangeSelector:
        {
            'enabled': false
        }, // takes away the 1W, 1Month, 1Yr, YTD options as well as zooming to specific dates
        yAxis:
        {
            labels:
            {
                x: -50,
                y: 0
            }
        }
    });

    // insert the highcharts menu option to clear the chart
    Highcharts.getOptions().exporting.buttons.contextButton.menuItems.splice(0,0,
    {
        text: 'Clear Chart',
        onclick: function()
        {
            reinit(0);
        }
    });

    // TODO: add download option
    /*Highcharts.getOptions().exporting.buttons.contextButton.menuItems.push(
    {
        text:'Download CSV',
        onclick: function()
        {
            alert('feature in development')
        }
    });*/

    // function to reinitialize the page in a bit more elegant way.
    // moved it out of the doc ready function to be in same scope as the clear chart button from highcharts menu
    function reinit(level)
    {
        switch(level)
        {
            case 0: //start over
                // remove all series from legend
                jQuery("#legend-inner-div").empty();
                // remove all series from chart
                var chart = jQuery('#highchart-placeholder').highcharts();
                while(chart.series.length > 1)
                {
                    chart.series[1].remove(true);
                }

                jQuery("#start-over-btn").addClass('disabled');
                jQuery("#download-series-btn").addClass('disabled');
                // reset global series counter
                seriesCount = 1;
                break; // don't care to continue through the rest of the reinit. This is only intended to clear
                       // out the series and not to reset the whole interface
            // purposefully no break statements so it creates a fall-through effect
            case 1: //change in scenario
                execIDObject = {};
                jQuery("#run-select-wrapper").hide();// hide run select
            case 2: //change in run
                // hide options
                jQuery("#channel-choice").hide();
                jQuery("#sweep-select-wrapper").hide();
                jQuery("#align-select-wrapper").hide();
                jQuery("#aggregation-select-wrapper").hide();

                // disable add data set button
                jQuery('#add-data-set-to-chart').addClass('disabled');
            }
        }

        $(document).ready(function()
        {
            $("#scenario-select-wrapper").show();

            // If we come to the page using /scenario/1234/ or /run/1234/, we need to manually fill execIDObject,
            // otherwise the value is 'default' and execIDObject will fill when a scenario is selected
            if ($('#scenario-select').val() != 'default')
            {
                $.ajax(
                {
                    type: "GET",
                    url: viewtastic_link + 'data/' + $('#scenario-select').val() + '/'
                }).success(function (run_data)
                {
                    for (var i in run_data)
                    {
                        execIDObject[run_data[i].id] = run_data[i].executions;
                    }
                });
            }

            $('#scenario-select').change(function()
            {
                reinit(1);
                $("#scenario-load-spinner").show();

                // TODO keep track of xhr request and abort it if the dropdown is changed again
                $.ajax(
                {
                    type: "GET",
                    url: viewtastic_link + 'data/' + $(this).val() + '/'
                }).success(function(run_data)
                {
                    // empty non-default elements
                    $("#run-select>option").each(function()
                    {
                        if ($(this).attr('value') != 'default')
                        {
                            $(this).remove();
                        }
                    });

                    for (var i in run_data)
                    {
                        $('#run-select').append('<option value="' + run_data[i].id + '">' + '(' + run_data[i].id + ') ' + run_data[i].name + '</option>');
                        execIDObject[run_data[i].id] = run_data[i].executions;
                    }

                    $("#run-select-wrapper").show();
                }).complete(function()
                {
                    $("#scenario-load-spinner").hide();// hide the spinner even if it is unsuccessful. TODO: Handle failed ajax call
                }); // end ajax
            });

            if( run_chosen_flag )
            {
                load_run_options();
            }

            $('#run-select').change(function()
            {
                load_run_options();
            }); // end run select change

            function load_run_options()
            {
                reinit(2);
                $("#run-load-spinner").show();

                // TODO keep track of xhr request and abort it if the dropdown is changed again
                $.ajax(
                {
                    type: "GET",
                    url: viewtastic_link + 'data/'+ $('#scenario-select').val() +'/' + $('#run-select').val() + '/keys/',
                    contentType: 'application/json'
                }).success(function(key_data)
                {
                    $("#sweep-select-div").empty();

                    // Add each key to the Sweeps select controls
                    // id naming scheme is typically <prefix>__[key_name]_<postfix> so that names can be passed around easier.
                    for (var i in key_data)
                    {
                        // doing string operations prior to the append for sake of readability.
                        var escapedId = key_data[i].name;
                        // removing everything up to the last slash, and replacing underscores with spaces
                        var accordionHeadingString = key_data[i].name.replace(/.*\//,'').replace(/_/g,' ');

                        // Build the header for the select dropdown
                        var sweepDiv = $('<div/>', {'class':'sweep-select'})
                            .append($('<label/>', {for:escapedId})
                                .text(accordionHeadingString)
                            // tooltip for the 'full string' of the sweep parameter if there are multiple sweeps of the same name
                            .append($('<i/>', {'data-toggle':"tooltip", title: key_data[i].name, class :"icon icon-info-sign", style:"margin-left:5px"})))
                            .append(function()
                            {
                                var the_options = $('<select/>', {'id': escapedId, 'data-mod-order': key_data[i].order});
                                for (var j in key_data[i].options)
                                {
                                    the_options.append(
                                        $('<option/>', {'value':key_data[i].options[j]}).text(key_data[i].options[j])
                                    )
                                }
                                return the_options;
                            });

                        // append the div and instantiate the tooltip
                        $('#sweep-select-div').append(sweepDiv);
                        $(".sweep-select").find('i').tooltip();
                    }

                    // only show the div if there are actually sweeps
                    if(key_data.length > 0)
                    {
                        $("#sweep-select-wrapper").show();
                    }
                // end .success
                }).complete(function()
                {
                    $("#run-load-spinner").hide();// hide the spinner even if it is unsuccessful. TODO: Handle failed ajax call
                });// end ajax


                // TODO keep track of xhr request and abort it if the dropdown is changed again
                $.ajax(
                {
                    type: "GET",
                    url: viewtastic_link + 'data/' + $('#scenario-select').val() + '/' + $('#run-select').val() + '/channels/',
                    contentType: 'application/json'
                }).success( function(new_data)
                {
                    $("#channel-select").empty(); // empty out the old channel options

                    var default_id = new_data[0].id;

                    // new_data will contain a dictionary with the channel id from the datawarehouse along with a readable type and title
                    for (var i in new_data)
                    {
                        var label = new_data[i].info.title;

                        // get rid of the silly ': null' types if it isn't applicable
                        if( new_data[i].info.type != null )
                        {
                            label += ": " + new_data[i].info.type;
                        }

                        // This is true only for Daily EIR without a particular species
                        if (new_data[i].info.title == "Daily EIR" && new_data[i].info.type == null)
                        {
                            default_id = new_data[i].id;
                        }

                        // add the channel with the id from dw as the value
                        $('#channel-select').append($('<option/>', {'value': new_data[i].id}).text(label));
                    } //end for each channel id

                    $('#channel-select').val(default_id).change();

                    // show appropriate divs if the channel request is successful
                    $('#channel-choice').show();
                    $('#align-select-wrapper').show();
                    $('#aggregation-select-wrapper').show();
                    $('#add-data-set-to-chart').removeClass('disabled');
                }); // end ajax
            } // end function load_run_options

            // actually get the data and add it to the chart
            $("#add-data-set-to-chart").click( function()
            {
                if( !$(this).hasClass('disabled') )
                {

                    // bring up the loading message and disable the add button. adding series is going to be a non-concurrent
                    // operation.
                    $("#dataset-loading-span").show();
                    $('#add-data-set-to-chart').addClass('disabled');

                    // ajaxObject will hold all of the options we are choosing when querying the server for the data series
                    var ajaxObject = {};
                    ajaxObject.run_id = $('#run-select').val();
                    ajaxObject.channel_id = $('#channel-select').val();

                    if( $('.sweep-select').length > 0 ) // there are sweeps with this run
                    {
                        ajaxObject.parameters = {};
                        $('.sweep-select>select').each(function()
                        {
                            ajaxObject.parameters[$(this).attr('id')] = {};
                            ajaxObject.parameters[$(this).attr('id')].values = [encodeURIComponent($(this).val().replace(/"/g,'\\"'))];
                            ajaxObject.parameters[$(this).attr('id')].mod_order = $(this).data('mod-order');
                        })
                    }
                    else // else put the execution id here instead
                    {
                        ajaxObject.execution = execIDObject[ajaxObject.run_id][0];
                    }

                    //ajaxObject.parameters = {'config.json/parameters/Base_Land_Temperature':["25.0"], 'config.json/parameters/Acquisition_Blocking_Immunity_Decay_Rate':["0.02"]};
                    ajaxObject.aggregation = $("#aggregation-option-select").val();

                    // hardcode some options since we don't have selectable choice for boxplot yet.
                    ajaxObject.chart_type = "time_series";
                    ajaxObject.outliers = false;
                    ajaxObject.boxplot = false;

                    // build a temporary div to return back to the correct div after series is returned.
                    // $('#element option:selected').text() gets the actual text of the dropdown option currently selected
                    var tempDiv = $('<div/>').data('channel-id',$('#channel-select option:selected').text()).data(
                                                   'scenario-id',$('#scenario-select option:selected').text()).data(
                                                   'run-id',$('#run-select option:selected').text());

                    tempDiv.data('sweeps',[]);
                    $(".sweep-select").each( function()
                    {
                        tempDiv.data('sweeps').push([$(this).children('label').text(),$(this).find('option:selected').text()]);
                    });

                    tempDiv.data('align', $('#align-option-select').val());
                    tempDiv.data('aggregation', $('#aggregation-option-select option:selected').text());

                    $("#legend-inner-div").append(tempDiv);

                    var loadURL = viewtastic_link + 'data/' + $("#scenario-select").val() + '/' + $("#run-select").val()  + '/data/';

                    currentXHR = $.ajax(
                    {
                        type: "POST",
                        url: loadURL,
                        data: JSON.stringify(ajaxObject),
                        contentType: "application/x-www-form-urlencoded",
                        timeout: 120000 // 120 second timeout just to make sure we eventually get back control of the div.
                    }).success(function(new_data)
                    {
                        var chart = $('#highchart-placeholder').highcharts();
                        //limiting the number of series that can be added to the chart to a conservative value
                        //TODO: Alert the user that they have reached their limit of series
                        if (chart.series.length <= 15)
                        {
                            var myDiv = $("#legend-inner-div div:last-child"); // this is safe since the series addition isn't concurrent

                            // add the series title and the collapse/expand/delete buttons
                            myDiv.append('<strong>Series #' + seriesCount  +
                                         '</strong>:<i class="pull-right icon icon-remove remove-series-btn"></i>' +
                                         '<i class="pull-right icon icon-chevron-down toggle-series-btn"></i><br/>');

                            // add the actual series options that were used when fetching the series
                            // added the span to be able to collapse the series legend if the user wants to
                            myDiv.append($('<span/>').append('<strong>Simulation:</strong> ' + myDiv.data('scenario-id') + '<br/>' +
                                         '<strong>Run:</strong> ' + myDiv.data('run-id') + '<br/>' +
                                         '<strong>Output:</strong> ' + myDiv.data('channel-id') + '<br/>'));

                            // if there were any sweeps, add those here
                            if( myDiv.data('sweeps').length > 0 )
                            {
                                myDiv.children('span').append('<strong>Sweeps:</strong> <br/>');
                                for(var i = 0 ; i < myDiv.data('sweeps').length ; i++)
                                {
                                    myDiv.children('span').append('&nbsp' + myDiv.data('sweeps')[i][0] + ' : ' + myDiv.data('sweeps')[i][1] + '<br/>');
                                }
                            }

                            // finally finish adding the options that were chosen.
                            myDiv.children('span').append('<strong>Time Alignment:</strong> ' + myDiv.data('align') + '<br/>');
                            myDiv.children('span').append('<strong>Aggregation:</strong> ' + myDiv.data('aggregation') + '<br/>');
                            myDiv.children('span').append('<br/>');

                            // build up the series and modify some of the highchart values before adding it to the chart
                            var tempSeries =
                            {
                                data: new_data['chart_JSON'].series[0].data, name: 'series #' + seriesCount,
                                pointInterval: new_data['chart_JSON'].series[0].pointInterval
                            };

                            seriesCount++;
                            $("#start-over-btn").removeClass('disabled');
                            $("#download-series-btn").removeClass('disabled');

                            // set start time based on alignment option
                            if ( myDiv.data('align') == 'Left' )
                            {
                                tempSeries.pointStart = 0;
                            }
                            else
                            {
                                tempSeries.pointStart = new_data['chart_JSON'].series[0].pointStart;
                            }

                            // add the series, then set the css on the legend div to match the series color on the chart
                            chart.addSeries(tempSeries);
                            myDiv.css("color", chart.series[chart.series.length - 1].color);
                        }
                    }).complete(function()
                    {
                        // give control back to the user even if it errors/times out
                        $("#dataset-loading-span").hide();
                        $('#add-data-set-to-chart').removeClass('disabled');
                    });  // end ajax
                } // end if <= 15 series
            }); // end add to chart button click

            // homebrew collapse/expand logic.
            $("#legend-inner-div").on('click', '.toggle-series-btn', function()
            {
                if( $(this).hasClass('collapsed') )
                {
                    $(this).closest('div').find('span').show();
                    $(this).removeClass('icon-chevron-right');
                    $(this).addClass('icon-chevron-down');
                    $(this).removeClass('collapsed');
                }
                else
                {
                    $(this).closest('div').find('span').hide();
                    $(this).removeClass('icon-chevron-down');
                    $(this).addClass('icon-chevron-right');
                    $(this).addClass('collapsed');
                }
            }); // end toggle button click

            // removes individual series from chart and legend
            $("#legend-inner-div").on('click', ".remove-series-btn", function()
            {
                //var seriesId = $(this).closest('div').attr('id').replace("series-legend-", "");

                var chart = $('#highchart-placeholder').highcharts();
                chart.series[$(this).closest('div').index() + 1].remove(true);
                $(this).closest('div').remove();
            }); // end remove button click

            // gives the user an option to stop waiting for the ajax call to return
            $("#cancel-fetch-link").click(function()
            {
                currentXHR.abort();

                // since the legend div is pre-added prior to successful return, we need to remove the last added div there
                $("#legend-inner-div div:last-child").remove();

                $("#dataset-loading-span").hide();
                $('#add-data-set-to-chart').removeClass('disabled');
            })
        }); // end document ready function.