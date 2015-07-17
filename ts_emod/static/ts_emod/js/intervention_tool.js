/**
 * Created by nreed on 5/12/15.
 */
var InterventionTool = InterventionTool || {};
InterventionTool.newInterventionList = [];
InterventionTool.interventionNamesList = [];
InterventionTool.interventionFormUrl = "";

$(function () {
  jQuery.validator.addMethod("notEqualTo",
      function(value, element, param) {
          var notEqual = true;
          value = $.trim(value).replace(" ", "_");
          for (i = 0; i < param.length; i++) {
              if (value == param[i]) { notEqual = false; }
          }
          return notEqual;
      },
      "An intervention with this name already exists. Please enter a different name."
  );

  var select = document.getElementById("type_select");
  //select.options[select.options.length] = new Option('Select a Type');

  /* loop through types provided */
  InterventionTool.newInterventionList.forEach(function(value, index) {
    /* add type to options list */
    var val = (value == 'Please select an intervention type') ? '' : value;
    select.options[select.options.length] = new Option(value, val);
  });

  /* Enable tooltips */
  $('.tooltip_link').tooltip({container: '#addNewModal', placement: 'top'});

  // Preload data if location is selected already
  if ($("#type_select").val()) {
    populate_form($("#type_select").val());
  }

  $("#type_select").change(function() {
    // Load form based on user's selection
    populate_form($(this).val());
  });

  /* Upload file form */
  $("#upload-div").show();
  //$.get("{% url 'ts_emod_upload' %}", function(data) {
      //$("#upload-div").html(data);
  //});

  // if any items in cart,
  // disable "Upload Campaign File" button modal function
  // - display alert message instead
  $('#upload_button').click(function(e) {
      if ($("ul.cart li").length < 1) {
          $("#upload_button").attr('data-toggle', 'modal');
      } else {
          alert("Please remove interventions from the selection list before uploading a file.");
          $("#upload_button").removeAttr('data-toggle');
      }
  });

  $("#save").validate({
    rules: {
      "my_name": {
        required: true,
        notEqualTo: InterventionTool.interventionNamesList
      }
    }
  });

  // #5683 - save and launch button
  $('#launch').click(function () {
      var input = $("<input>")
                 .attr("type", "hidden")
                 .attr("name", "launch").val('1');
      $('#interventionForm').append($(input));
  });
});

function populate_form(form_name) {
  if (!form_name) {
    return false;
  }
  $.get(InterventionTool.interventionFormUrl + form_name, function(data) {
    var jsonField = $("#json-field");
    jsonField.show();
    jsonField.html(data);

    /* Enable tooltips for the newly loaded fields */
    $('.tooltip_link').tooltip({container: '#addNewModal', placement: 'top'});
  });
}
function hide_info() {
  $("#info").popover("hide");
}


