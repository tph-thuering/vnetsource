/*######################################################################################################################
 * # VECNet CI - Prototype
 * # Date: 4/5/2013
 * # Institution: University of Notre Dame
 * # Primary Authors:
 * #   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
 * #   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
 * ######################################################################################################################*/

/* This is the javascript file to be used with q-unit unit testing.
 *
 * The tests contained herein are more like functional tests.  These tests are for the datawarehouse and
 * will be testing javascript specific functions.  Other tests will be run with selenium.
 *
 * TODO Use one source of tests instead of two (q-unit and selenium)
*/

/* This test is concerned with the "Add All" links for dimensions and measures
 *
 * This will use the add all links for dimensions and measures and ensures that all
 * dimensions and measures located in the dimensions and measures divs are present
 */
asyncTest("Add All Basics",function(){
    var cube_options = $('#cube option');
    var selection = $(cube_options[3]).attr('value');
    $('#cube').val(selection);
    $('#cube').trigger('change');
    setTimeout( function(){
        $('#dataset_holder p a').trigger('click'),
        $('#dimensions .dim').each(function(){
            var ident = $(this).attr('id');
            var that = $('#xdiv').find('[data-name="' + ident + '"]').attr('data-name');
            equal(ident,that);
        });
        $('#measures .meas').each(function(){
            var ident = $(this).attr('id');
            var that = $('#ydiv').find('[data-name="' + ident +'"]').attr('data-name');
            equal(ident,that);
        });
        start();},
        1000
    );
});

asyncTest("Create Graphs",function(){
    var cube_options = $('#cube option');
    var selection = $(cube_options[3]).attr('value');
    $('#cube').val(selection);
    $('#cube').trigger('change');
    setTimeout( function(){
        $('#dataset_holder p a').trigger('click'),
        $('#dimensions .dim').each(function(){
            var ident = $(this).attr('id');
            var that = $('#xdiv').find('[data-name="' + ident + '"]').attr('data-name');
            equal(ident,that);
        });
        $('#measures .meas').each(function(){
            var ident = $(this).attr('id');
            var that = $('#ydiv').find('[data-name="' + ident +'"]').attr('data-name');
            equal(ident,that);
        });
        start();
        stop();
        $('#create_graph').trigger('click');
        setTimeout( function(){
            start();
            equal($('.chart').length,4);
        },25000);
    },1000);
});
