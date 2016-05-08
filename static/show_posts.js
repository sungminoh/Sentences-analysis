var topic;
var sources;
var ruleText;
var ishover;
//var category_seq;

var create_rule_checkbox = function(morphs) {
    $.each(morphs, function(){
        var morph = this;
        var word = this[0];
        $('#rule-checkboxes').append(
            $('<div>').attr({
                'class': 'checkbox',
                'style': 'display:inline-block; margin:5px'
            }).append(
                $('<label>').text(word).prepend(
                    $('<input>').attr({
                        'type': 'checkbox',
                        'class' : 'word-checkbox',
                        'name': 'word-selection'
                    }).val(morph.join('_'))
                )
            )
        )
    });
};
var get_checked_rules = function(category_seq){
    var ret = [];
    $('input:checkbox[name=word-selection]:checked').each(function(){
        ret.push($(this).val());
    });
    return ret;
};
var empty_checkboxes = function(){
    $('#rule-checkboxes').empty();
};

var show_posts = function(posts){
    $.each(posts, function(){
        $('#posts').append(
            $('<tr>').prepend(
                $('<td>').text(this.title),
                $('<td>').text(this.text)
            )
        );
    });
};

var show_rules = function(category_seq, rules){
    $('#ruleset-menu-'+category_seq).empty();
    $.each(rules, function(){
        var rule_id= this.rule_id;
        var full_text = this.full_text;
        var words = this.word;
        $('#ruleset-menu-'+category_seq).append(
            $('<li>').attr({
                'id':'rule-li-'+rule_id
            }).append(
                $('<a>').attr({
                    'class':'clearfix',
                    'id':'rule-a-'+rule_id 
                }).text(full_text).append(
                    $('<span>').attr({'class':'pull-right'}).append(
                        $('<button>').attr({
                            'class':'btn btn-warning btn-xs glyphicon glyphicon-remove ruleset-button',
                            'value':rule_id,
                            'name':'delete-rule-btn'
                        })
                    )
                )
            )
        );
        $.each(words, function(){
            $('#rule-a-'+rule_id).append(
                $('<span>').attr({
                    'class':'label label-default',
                    'style':'margin:3px'
                }).text(this)
            )
        });
    });
    $(document).on('click', 'button[name=delete-rule-btn]', function(){
        var rule_id = this.value
        jQuery.ajax({
            type: 'DELETE',
            url: '/_rules',
            data: {
                'rule_id':rule_id 
            },
            dataType: 'JSON',
            success: function(data){
                $('#rule-li-'+rule_id).remove()
            },
            error: function(xhr, status, error){
                console.log('get rules failed');
            }
        });
    });

}

var show_rulesets = function(rulesets){
    $('#ruleset-creator-ul').css('display', 'block');
    $.each(rulesets, function(){
        var category_seq = this.category_seq;
        var name = this.name;
        $('#rulesets').prepend(
            $('<li>').attr({
                'class':'dropdown',
                'name':'ruleset-dropdown',
                'id':'ruleset-dropdown-'+category_seq
            }).append(
                $('<a>').attr({
                    'class':'dropdown-toggle clearfix',
                    'data-toggle':'dropdown',
                    'name':'ruleset-a',
                    'value':category_seq,
                    'id':'ruleset-a-'+category_seq
                }).text(name).append(
                    $('<span>').attr({'class':'pull-right'}).append(
                        $('<button>').attr({
                            'class':'btn btn-info btn-xs glyphicon glyphicon-file ruleset-button',
                            'style':'margin-right:5px',
                            'value':category_seq,
                            'name':'create-rule-modal-btn',
                            'data-toggle':'modal',
                            'data-target':'#create-rule-modal'
                        }),
                        $('<button>').attr({
                            'class':'btn btn-warning btn-xs glyphicon glyphicon-remove ruleset-button',
                            'value':category_seq,
                            'name':'delete-ruleset-btn'
                        })
                    )
                ),
                $('<ul>').attr({
                    'class':'dropdown-menu navmenu-nav',
                    'name':'ruleset-menu',
                    'id':'ruleset-menu-'+category_seq,
                    'role':'menu'
                })
            )
        );
    });
    $(document).on('click', 'a[name=ruleset-a]', function(){
        if(ishover){return}
        var category_seq = this.getAttribute('value');
        jQuery.ajax({
            type: 'GET',
            url: '/_rules',
            data: {
                'topic': topic,
                'category_seq': category_seq 
            },
            dataType: 'JSON',
            success: function(data){
                show_rules(category_seq, data.rules)
            },
            error: function(xhr, status, error){
                console.log('get rules failed');
            }
        });
    });
    $(document).on('click', 'button[name=create-rule-modal-btn]', function(){
        $('#parse').attr({'value': this.value});
    });
    $(document).on('click', 'button[name=delete-ruleset-btn]', function(){
        var category_seq = this.value
        jQuery.ajax({
            type: 'DELETE',
            url: '/_rulesets',
            data: {
                'topic': topic,
                'category_seq': category_seq
            },
            dataType: 'JSON',
            success: function(data){
                $('#ruleset-a-'+category_seq).empty()
                $('#ruleset-a-'+category_seq).remove()
            },
            error: function(xhr, status, error){
                console.log('get rules failed');
            }
        });
    });
    $(document).on({
            'mouseenter': function(){
                //$('a[name=ruleset-a]').click(function(){return false});
                ishover = true;
            },
            'mouseleave': function(){
                //$('a[name=ruleset-a]').unbind('click');
                ishover = false;
            }
        }, '.ruleset-button'
    );
};

var clear_posts = function(){
    $('#posts').empty()
}
var clear_rulesets = function(){
    $('#rulesets').empty()
}

var main = function(){
    var httpRequest;
    $('#sources').selectpicker('selectAll');
    $('#getPosts').click(function(){
        topic = $("#topics").val();
        sources = $("#sources").val();
        jQuery.ajax({
            type: 'GET',
            url: '/_posts',
            data: {
                'topic': JSON.stringify(topic),
                'sources': JSON.stringify(sources)
            },
            dataType: 'JSON',
            success: function(data){
                clear_posts();
                clear_rulesets();
                show_posts(data.posts);
                show_rulesets(data.rulesets);
            },
            error: function (xhr, status, error){
                console.log('get posts ajax errrr')
            }
        });
    });
    $('#ruleset-creator-btn').click(function(){
        rulesetName = $('#ruleset-creator-txt').val();
        jQuery.ajax({
            type: 'POST',
            url: '/_rulesets',
            data: {
                'topic': topic,
                'name': rulesetName
            },
            dataType: 'JSON',
            success: function(data){
                show_rulesets(data.rulesets);
                $('#ruleset-creator-txt').val('')
            },
            error: function(xhr, status, error){
            }
        });
    });
    $('#parse').click(function(){
        ruleText = $('#rule-text').val();
        jQuery.ajax({
            type: 'GET',
            url: '/_parsing',
            data: {'text': ruleText},
            dataType: 'JSON',
            success: function(data){
                empty_checkboxes()
                create_rule_checkbox(data.morphs);
            },
            error: function(xhr, status, error){
                console.log('parse ajax errrrrrrr');
            }
        });
    });
    $('#create-rule-reset-btn').click(function(){
        ruleText = '';
        $('#rule-text').val('');
        empty_checkboxes()
    });

    $('#create-rule-btn').click(function(){
        checked = get_checked_rules();
        var category_seq = $('#parse').val();
        jQuery.ajax({
            type: 'POST',
            url: '/_rules',
            data: {
                'topic': topic,
                'category_seq': category_seq,
                'ruleText': ruleText,
                'checked': JSON.stringify(checked)
            },
            dataType: 'JSON',
            success: function(data){
                console.log(data.checked);
            },
            error: function(xhr, status, error){
                console.log('rule is not posted');
            }
        });
    });

    $('#run').click(function(){
    });

};

$(document).ready(main);

