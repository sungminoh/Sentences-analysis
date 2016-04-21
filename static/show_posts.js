var create_checkbox = function(result) {
    $.each(result, function (i, v) {
        $('#checkboxes').append(
            $('<div>').attr({'class': 'checkbox'}).prepend(
                $('<label>').text(this[0]).prepend(
                    $("<input>").attr({
                        'type': 'checkbox', 
                        'class' : 'inp-checkbox'
                    }).val(this.join('_'))
                )
            )
        );
    });
};

var create_register_button = function() {
    $('#checkboxes').append(
        $('<button>').text('Register').attr({
            'type': 'button',
            'class': 'btn btn-default',
            'id': 'register'
        })
    )
};

var main = function() {
    var httpRequest;
    $('#parse').click(function() {
        jQuery.ajax({
            type: 'GET',
            url: '/parsing',
            data: {'text': $('#rule_text').val()},
            dataType: 'JSON',
            success: function(data){
                create_checkbox(data.result);
                create_register_button();
            },
            error: function(xhr, status, error){
                alert('errrrrrrr');
            }
        });
    });
};

$(document).ready(main);
