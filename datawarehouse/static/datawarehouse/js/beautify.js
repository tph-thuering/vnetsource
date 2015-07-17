/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/

"use strict";
/* Capitalized all of the words in a string seperated by whitespace
 *
 * Input arguments
 *  in_string:      The string that is to be capitalized
 *
 * Output arguments
 *  out_string:     The capitalized string*/
function capitalize(in_string){
    var out_string=in_string.toLowerCase().replace(/\b[a-z]/g, function(letter){
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
function beautify(in_string){
    in_string = in_string.replace("date_cubes", "Date");
    in_string = in_string.replace(/_/g," ");
    in_string = in_string.replace("percent","%");
    in_string = in_string.replace("gte",">=");
    in_string = in_string.replace("lt","<");
    in_string = in_string.replace("number","#");
    in_string = in_string.replace("years","yrs");
    in_string = in_string.replace("one","1");
    in_string = in_string.replace("five","5");
    in_string = in_string.replace("nmbr","#");
    in_string = in_string.replace("dlvrd","delivered");
    in_string = in_string.replace("pcnt","%");
    in_string = in_string.replace("ndx","index");
    in_string = in_string.replace("trtmnt","treatment");
    in_string = in_string.replace("incldng","including");
    in_string = in_string.replace(" hh "," household ");
    in_string = in_string.replace("chldrn","children");
    in_string = in_string.replace(" rel "," relative ");
    in_string = in_string.replace("cvrg","coverage");
    in_string = in_string.replace(" preg"," pregnant");
    in_string = in_string.replace(" cnt"," count");
    in_string = in_string.replace(" spd"," speed");
    in_string = in_string.replace(" sus"," sustained");
    in_string = in_string.replace(" precip"," precipitation");
    in_string = in_string.replace(" sl"," sea level");
    in_string = in_string.replace(" dewpnt"," dew point");
    in_string = in_string.replace(" obs"," observation");
    in_string = in_string.replace(" vis"," visibility");
    in_string = in_string.replace("eir", "EIR");
    in_string = capitalize(in_string);
    return in_string;
}
