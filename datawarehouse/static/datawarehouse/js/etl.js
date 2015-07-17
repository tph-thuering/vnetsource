var mapArray = new Array();
    
$(document).ready(function() {
    $('.dbDraggable').draggable({
        containment:"window",
        cursor:"move",
        helper:"clone",
        revert:'invalid',
     });
    
    $('.inputDraggable').draggable({
        containment:"window",
        cursor:"move",
        helper:"clone",
        revert:'invalid',
     });
        
    $('#inputDrop').droppable({
        accept: ".inputDraggable",
        drop: function(event, ui){
            $(this).find('p').hide();
            $(this).append(ui.draggable);
            $(this).droppable({ accept: ui.draggable });
        },
    });
    
    $('#dbDrop').droppable({
        accept: ".dbDraggable",
        drop: function(event, ui){
            $(this).find('p').hide();
            $(this).append(ui.draggable);
            $(this).droppable({ accept: ui.draggable });
        },
    });
    
    $(document).on('click', '.rmvbtn', function(){
        // get the current index of the clicked button's row. detach the mapping objects,
        // remove their mapped class, and reattach them to their original containers.
        // remove the row as well
        var prnt = $(this).parent();
        var artxt = prnt.children().eq(2).text()+"::"+prnt.children().eq(1).text();
        prnt.children().eq(0).remove();
        prnt.children().eq(0).detach().removeClass('mapped').appendTo('#inputcolumns');
        mapArray = remove_item(mapArray, artxt);
        $('#id_createMap-mapping').attr('value', mapArray.join());
        prnt.children().eq(0).detach().removeClass('mapped').appendTo('#dbcolumns');
        prnt.remove();
    });
});

function addMap(icol, dcol){
    var i = $(icol).find('.inputDraggable').text();
    var d = $(dcol).find('.dbDraggable').text();
    
    if( d != "" && i != ""){
        rowtxt = "<div class=\"mappingrow\"></div>"
        var rw = $(rowtxt).appendTo('#fulloutput');
        btntxt = "<a class=\"pull-left rmvbtn\"><i class=\"icon-remove\"></i></a> "
        rw.append(btntxt)
        rw.append($(icol).find('.inputDraggable').addClass("mapped"));
        rw.append($(dcol).find('.dbDraggable').addClass("mapped"));        
        mapArray.push(d+"::"+i);
        $(icol).find('.inputDraggable').remove();
        $(dcol).find('.dbDraggable').remove();
        $('#dbDrop').find('p').show();
        $('#dbDrop').droppable({ accept: ".dbDraggable" });
        $('#inputDrop').find('p').show();
        $('#inputDrop').droppable({ accept: ".inputDraggable" });
    }
    else{
        alert("You must provide one input column and one database column.");
        return false;
    }
    
    $('#id_createMap-mapping').attr('value', mapArray.join());
    return true;
}

function remove_item(arr,value){
    for(b in arr ){
        if(arr[b] == value){
            arr.splice(b,1);
            break;
        }
    }
    return arr;
}