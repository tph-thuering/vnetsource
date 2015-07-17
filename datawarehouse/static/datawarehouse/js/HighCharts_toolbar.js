/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/

/* This file contains the code required to add a toolbar to HighCharts*/

(function($){
    var caller = '';
    var methods = {
        init : function(obj){
            this.data('chart',obj.chart_obj);
            caller = this;
            return this.each(function(){
                var target = $(this);
                var target_id = $(this).attr('id');
                var chart_types = {
                    'Line':'line',
                    'Bar':'bar',
                    'Scatter':'scatter',
                    'Area':'area',
                    'Pie':'pie'
                };
                var title_types = {
                    'Title':'title',
                    'SubTitle':'subtitle',
                    'xAxis Title':'xAxis',
                    'yAxis Title':'yAxis'
                };
                
                //Add window options
                var window_div = document.createElement('div');
                $(window_div).append('Window: ');
                $(window_div).addClass('hctoolbar_row');
                var btn_div = document.createElement('div');
                $(btn_div).addClass('btn-group');
                $(btn_div).append('<button class="btn dropdown-toggle" data-toggle="dropdown" type="button"><i class="icon-bar-chart"></i><span class="caret"></span></button>');
                var ul_div = document.createElement('ul');
                $(ul_div).addClass('dropdown-menu');
                $.each(chart_types,function(key,value){
                    li = document.createElement('li');
                    $('<a></a>')
                        .attr('href','javascript:void(0)')
                        .bind('click',function(){
                            methods.changeOption(target,'chart','type',value);
                        })
                        .text(key)
                        .appendTo(li);
                    $(ul_div).append(li);
                });
                $(btn_div).append(ul_div);
                $(window_div).append(btn_div);
                $('<a></a>')
                    .addClass('btn')
                    .attr('id','toolbar_windowbg_cp')
                    .attr('data-color-format','hex')
                    .attr('data-color','rgb(255,255,255)')
                    .attr('data-toggle','tooltip')
                    .attr('title','Window Background Color')
                    .append('<i class="icon-circle"></i>')
                    .appendTo(window_div);

                $('<a></a>')
                    .addClass('btn')
                    .attr('id','toolbar_windowbrdr_cp')
                    .attr('data-color-format','hex')
                    .attr('data-color','rgb(255,255,255)')
                    .attr('data-toggle','tooltip')
                    .attr('title','Window Border Color')
                    .append('<i class="icon-circle-blank"></i>')
                    .appendTo(window_div);
                $('<a></a>')
                    .addClass('btn')
                    .attr('id','toolbar_invert')
                    .attr('data-toggle','tooltip')
                    .attr('title','Ivert Axes')
                    .bind('click',function(){
                        methods.changeOption(target,'chart','inverted','toggle')
                    })
                    .append('<i class="icon-retweet"></i>')
                    .appendTo(window_div);

                // Add Plot options
                var plot_div = window_div;
                $(plot_div).append('| Plot: ');
                $('<a></a>')
                    .addClass('btn')
                    .attr('id','toolbar_plotbg_cp')
                    .attr('data-color-format','hex')
                    .attr('data-color','rgb(255,255,255)')
                    .attr('data-toggle','tooltip')
                    .attr('title','Plot Background Color')
                    .append('<i class="icon-circle"></i>')
                    .appendTo(plot_div);
                $('<a></a>')
                    .addClass('btn')
                    .attr('id','toolbar_plotbrdr_cp')
                    .attr('data-color-format','hex')
                    .attr('data-color','rgb(255,255,255)')
                    .attr('data-toggle','tooltip')
                    .attr('title','Plot Border Color')
                    .append('<i class="icon-circle-blank"></i>')
                    .appendTo(plot_div);

                // Add text options
                var text_div = window_div
                $(text_div).append('| Text: ');
                var input_div = document.createElement('div');
                $(input_div).addClass('input-append');
                $(input_div).append('<input id="toolbar_graph_text" type="text" placeholder="Text">');
                var btn_div = document.createElement('div');
                $(btn_div).addClass('btn-group');
                $(btn_div).append('<button class="btn dropdown-toggle" type="button" data-toggle="dropdown">Change Text <span class="caret"></span></button>');
                var ul_div = document.createElement('div');
                $(ul_div).addClass('dropdown-menu');
                $.each(title_types, function(key,value){
                    var li = document.createElement('li');
                    $('<a></a>')
                        .attr('href','javascript:void(0)')
                        .attr('onclick','changeText("' + value + '")')
                        .bind('click',function(){
                            methods.changeText(target,value);
                        })
                        .text(key)
                        .appendTo(li);
                    $(ul_div).append(li);
                });
                $(btn_div).append(ul_div);
                $(input_div).append(btn_div);
                $(text_div).append(input_div);

                // Add Axis options
                var axis_div = document.createElement('div');
                $(axis_div).append('Y Axis Type');
                var y_select = document.createElement('select');
                $(y_select).attr('id','toolbar_y_type');
                $(y_select).attr('data-axis','yAxis');
                $(y_select).append($('<option />').val("linear").text("Linear"));
                $(y_select).append($('<option />').val("logarithmic").text("Logarithmic"));
                $(y_select).bind('change',function(){
                    methods.changeOption(target,$(this).attr('data-axis'),'type',$(this).val());
                });
                $(axis_div).append(y_select);
                var x_select = document.createElement('select');
                $(x_select).attr('id','toolbar_x_type');
                $(x_select).attr('data-axis','xAxis');
                $(x_select).append($('<option />').val("linear").text("Linear"));
                $(x_select).append($('<option />').val("logarithmic").text("Logarithmic"));
                $(x_select).bind('change',function(){
                    methods.changeOption(target,$(this).attr('data-axis'),'type',$(this).val());
                });
                $(axis_div).append('| X Axis Type: ');
                $(axis_div).addClass('hctoolbar_row');
                $(axis_div).append(x_select);
                
                // Legend Options
                legend_div = document.createElement('div');
                $(legend_div).addClass('hctoolbar_row');
                $(legend_div).append('Legend Options: ');
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_left')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Left')
                    .append('<i class="icon-align-left"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','align','left');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_center')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Center')
                    .append('<i class="icon-align-center"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','align','center');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_right')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Right')
                    .append('<i class="icon-align-right"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','align','right');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_top')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Top')
                    .append('LAT')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','verticalAlign','top');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_middlet')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Middle')
                    .append('LAM')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','verticalAlign','middle');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_bottom')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend Align Bottom')
                    .append('LAB')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','verticalAlign','bottom');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_float')
                    .attr('data-toggle','tooltip')
                    .attr('title','Legend float, whether the legend floats on the graph or not')
                    .append('<i class="icon-beer"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','floating','toggle');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_horiz_layout')
                    .attr('data-toggle','tooltip')
                    .attr('title','Horizontal Legend Layout (Default)')
                    .append('<i class="icon-resize-horizontal"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','layout','horizontal');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_vert_layout')
                    .attr('data-toggle','tooltip')
                    .attr('title','Vertical Legend Layout')
                    .append('<i class="icon-resize-vertical"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','layout','vertical');
                    })
                    .appendTo(legend_div);
                $('<a></a>')
                    .addClass('btn legend-opt')
                    .attr('id','legend_rtl')
                    .attr('data-toggle','tooltip')
                    .attr('title','Reverse symbol and text in legend')
                    .append('<i class="icon-retweet"></i>')
                    .bind('click',function(){
                        methods.changeOption(target,'legend','rtl','toggle');
                    })
                    .appendTo(legend_div);
                $(legend_div).append('<a class="btn" id="toolbar_legendbg_cp" data-color-format="hex" data-color="rgb(255,255,255)" data-toggle="tooltip" title="Legend Background Color"><i class="icon-circle"></i></a>');
                $(legend_div).append('<a class="btn" id="toolbar_legendbrdr_cp" data-color-format="hex" data-color="rgb(255,255,255)" data-toggle="tooltip" title="Legend Border Color"><i class="icon-circle-blank"></i></a>');

                // Add this to the selected element
                // Put Plot and Window on the same line
                target.append(window_div);
                target.append(axis_div);
                target.append(legend_div);

                // Initialize dropdowns and colorpickers
                $('.dropdown-toggle').dropdown();
                $('#toolbar_windowbg_cp').colorpicker().on('changeColor',function(ev){
                    changeOption(target,'chart','backgroundColor',ev.color.toHex());
                });
                $('#toolbar_windowbrdr_cp').colorpicker().on('changeColor',function(ev){;
                    changeOption(target,'chart','borderColor',ev.color.toHex());
                });
                $('#toolbar_plotbg_cp').colorpicker().on('changeColor',function(ev){;
                    changeOption(target,'chart','plotBackgroundColor',ev.color.toHex());
                });
                $('#toolbar_plotbrdr_cp').colorpicker().on('changeColor',function(ev){;
                    changeOption(target,'chart','plotBorderColor',ev.color.toHex());
                });
                $('#toolbar_legendbg_cp').colorpicker().on('changeColor',function(ev){;
                    changeOption(target,'legend','backgroundColor',ev.color.toHex());
                });
                $('#toolbar_legendbrdr_cp').colorpicker().on('changeColor',function(ev){;
                    changeOption(target,'legend','borderColor',ev.color.toHex());
                });
                $('[data-toggle="tooltip"]').tooltip();
            });
        },

        changeOption: function(elem,obj,option,style){
            chart = elem.data('chart');
            if ( chart == undefined){return;}        // CHeck for charts existence
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
            elem.data('chart', new_chart);
        },

        changeText: function(elem,title_type){
            var text_val = $('#toolbar_graph_text').val();
            chart = elem.data('chart');
            switch(title_type){
                case 'title': chart.setTitle({ text: text_val }); break;
                case 'subtitle': chart.setTitle(null, { text: text_val }); break;
                case 'xAxis': chart.xAxis[0].setTitle({ text: text_val }); break;
                case 'yAxis': chart.yAxis[0].setTitle({ text: text_val }); break;
                default:return
            }
        }
    };

    $.fn.HCToolbar = function( method ){
        if ( methods[ method ] ){
            return methods[ method ].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if ( typeof method === 'object' || ! method ){
            return methods.init.apply( this, arguments );
        } else {
            $.error('Method' + method + ' does not exist on jQuery.HCToolbar' );
        }
    };
})(jQuery);
