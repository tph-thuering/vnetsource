/**
 *
 * Created by nreed on 6/23/15.
 */
$(function () {
  var modeTabsObj = $("#mode-tabs");
  modeTabsObj.find("a[href='#advanced']").on("click", getUpdatedScenario);

  $("#deployments").addClass("active");

  $(".deployments").on("click", ".delete-deployment", function() {
    var deploymentObj = $(this).parent();
    var prefix = "deployment";
    var deploymentIndex = $(".deployments").find(".deployment").index(deploymentObj);

    removeDeployment(deploymentIndex);

    var totalFormObj = $("#id_" + prefix + "-TOTAL_FORMS");
    var totalFormCount = parseInt(totalFormObj.val());

    totalFormObj.val(--totalFormCount);

    deploymentObj.remove();
  });

  $("#create").click(function() {
    var prefix = "deployment";
    var newFormObj = $($(".empty-form-" + prefix).clone(false).get(0));
    var totalFormObj = $("#id_" + prefix + "-TOTAL_FORMS");
    var totalFormCount = parseInt(totalFormObj.val());

    newFormObj.find("label").each(function () {
      if ($(this).attr("for")) {
        updateFormElement($(this), "for", "__prefix__", totalFormCount);
      }
    });

    newFormObj.find("input").each(function () {
      if ($(this).attr("id")) {
        updateFormElement($(this), "id", "__prefix__", totalFormCount);
      }
      if ($(this).attr("name")) {
        updateFormElement($(this), "name", "__prefix__", totalFormCount);
      }
    });

    newFormObj.find("select").each(function () {
      if ($(this).attr("id")) {
        updateFormElement($(this), "id", "__prefix__", totalFormCount);
      }
      if ($(this).attr("name")) {
        updateFormElement($(this), "name", "__prefix__", totalFormCount);
      }
    });

    var emptyIdPrefixStr = "#id_" + prefix + "-__prefix__-";
    var nameElement = $(emptyIdPrefixStr + "name");
    var timestepsElement = $(emptyIdPrefixStr + "timesteps");
    var coveragesElement = $(emptyIdPrefixStr + "coverages");
    var componentsElement = $(emptyIdPrefixStr + "components");
    var name = nameElement.val();
    var timesteps = timestepsElement.val();
    var coverages = coveragesElement.val();
    var components = componentsElement.val();

    nameElement.val("");
    timestepsElement.val("0");
    coveragesElement.val("0.0");
    componentsElement.val(componentsElement.find("option:first").val());

    var deploymentsObj = $(".deployments");
    deploymentsObj.append(newFormObj.html());

    var newIdPrefixStr = "#id_" + prefix + "-" + totalFormCount + "-";
    $(newIdPrefixStr + "name").val(name);
    $(newIdPrefixStr + "timesteps").val(timesteps);
    $(newIdPrefixStr + "coverages").val(coverages);
    $(newIdPrefixStr + "components").val(components);

    var deploymentObj = deploymentsObj.find(".deployment:last");
    deploymentObj.find(".delete-deployment").show();

    totalFormObj.val(++totalFormCount);
  });
});

function updateFormElement(elem, attr, splitStr, nr) {
  var split = elem.attr(attr).split(splitStr);
  var newStr = split[0] + nr + split[1];

  elem.attr(attr, newStr);
}

function removeDeployment(index) {
  $(".deployments").find(".deployment:visible").filter(function() {
    return $(".deployments").find(".deployment").index($(this)) > index;
  }).each(function(innerIndex) {
    var oldIndex = $(".deployments").find(".deployment").index($(this));
    var newIndex = index + innerIndex;

    $(this).find("label").each(function () {
      if ($(this).attr("for")) {
        updateFormElement($(this), "for", oldIndex, newIndex);
      }
    });

    $(this).find("input").each(function () {
      if ($(this).attr("id")) {
        updateFormElement($(this), "id", oldIndex, newIndex);
      }
      if ($(this).attr("name")) {
        updateFormElement($(this), "name", oldIndex, newIndex);
      }
    });

    $(this).find("select").each(function () {
      if ($(this).attr("id")) {
        updateFormElement($(this), "id", oldIndex, newIndex);
      }
      if ($(this).attr("name")) {
        updateFormElement($(this), "name", oldIndex, newIndex);
      }
    });
  });
}
