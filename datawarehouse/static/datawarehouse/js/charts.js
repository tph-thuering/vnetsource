/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/
"use strict";
//  This method constructs and returns a JSON object that can be used
//  by HighCharts to draw a chart.
//  @param cType: The chart type.
//  @param cTitle: The chart title.
//  @param xData: An array containing the x-axis categories
//  @param yData: An array of dictionaries. Each dictionary corrresponds to a
//                data series. The dictionary should contain the keys 'name'
//                and 'data'. Name is a string and data is an array holding
//                the series values.
//  @param xTitle: The title of the x axis.
//  @param yTitle: The title of the y axis.
function getChart(Element, cType, cTitle, xData, xTitle, yData, yTitle){
    var chart = {
        chart: {
            renderTo: Element[0],
            type: cType,
            inverted: false,
            zoomType: 'xy',
            width: 650,
            height: 650
        },
        scrollbar: {
            enabled: true
        },
        title: {
            text: cTitle
        },
        xAxis: {
            max: null,
            min: null,
            title:{
                text: xTitle
            },
            categories: xData,
            labels:{
                rotation:270,
                formatter: function(){
                    var data_index = xData.indexOf(this.value);
                    var chart_index = this.axis.tickPositions.indexOf(data_index);
                    var numcat = this.axis.tickPositions.length;
                    if(numcat < 50){
                        // If there are less than 50, inlcude all labels
                        return this.value;
                    }else{
                        var numtoskip = Math.round(numcat/50);
                        if(chart_index % numtoskip) {
                            return this.value;
                        }else{
                            return;
                        }
                    }
                }
            }
        },
        yAxis: {
            title: {
                text: yTitle
            }
        },
        series: yData,
        exporting: {
            enabled: true
        },
        navigation: {
            buttonOptions: {
                enabled: true
            }
        },
        credits: {
            enabled: true
        },
        tooltip: {
            valueDecimals: 2
        }
    };
    return chart
}
