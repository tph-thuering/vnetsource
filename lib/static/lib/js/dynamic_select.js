// return an ***ARRAY*** (do not treat it like an associative array) of keys
// sorted according to the values in the associative array (obj)
function getSortedKeys(obj) {
    var keys = Object.keys(obj);
    return keys.sort(function(a,b){return obj[a] > obj[b]}); // value string comparison
}

// clear out a select object (by object)
function clear_select(select_object){
    select_object.options.length = 0;
}

// clear out a select object (by object)
function clear_select_by_name(name){
    // get a handle on the selection of interest
    var select_object = document.getElementById(name);
    if (select_object==null){
	return;
    }
    select_object.options.length = 0;
}

// add a single option to an existing select object (by object)
function add_select_option(select_object, value, text){
    if ( select_object && text){
	var option = document.createElement('option');
	option.value = value;
	option.textContent = text;
	select_object.add(option);
    }
}

// completely empty and refill a select object (by name)
// with the contents of a dictionary  
function update_select(objectname, dictionary, defaultval){
    // get a handle on the selection of interest
    var selectBox = document.getElementById(objectname);
    if (selectBox==null){
	return;
    }
    clear_select(selectBox);
    
    if (dictionary && Object.keys(dictionary).length){
	
	// add each of the entries in the dictionary to the box
	// (alphabetically on values, thanks to getSortedKeys)
	var skeys = Object.keys(dictionary).sort();
	for (var i=0; i<skeys.length; i++){
	    add_select_option(selectBox, skeys[i], dictionary[skeys[i]]);
	}
	selectBox.selectedIndex=defaultval;
    } else {
	add_select_option(selectBox, 0, 'NONE');
    }
}
