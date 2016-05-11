var topic;
var sources;
var ruleText;
var ishover;
var colors = "#e53939,#b2ff80,#3333cc,#661a1a,#073300,#7979f2,#cca099,#00ff00,#1d1a33,#330e00,#00ffaa,#a099cc,#f26100,#00997a,#583973,#732e00,#004033,#9b00a6,#e5a173,#ace6da,#ff00ee,#b39e86,#00e2f2,#40103d,#73561d,#4d8a99,#ff80d5,#e5b800,#00aaff,#ffbfea,#333000,#004b8c,#804059,#f2ff40,#b6d6f2,#cc335c,#a4b386,#434f59,#332628,#448000,#000f73".split(',')

function convertHex(hex,opacity){
    hex = hex.replace('#','');
    r = parseInt(hex.substring(0,2), 16);
    g = parseInt(hex.substring(2,4), 16);
    b = parseInt(hex.substring(4,6), 16);
    result = 'rgba('+r+','+g+','+b+','+opacity/100+')';
    return result;
}

function get_ruleset_by_rule(rule_id){
    return parseInt($('#rule-li-'+rule_id).parent()[0].id.split('-').pop());
}


var create_rule_checkbox = function(morphs) {
    var i = -1;
    $.each(morphs, function(){
        i += 1;
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
                    }).val(i.toString()+'_'+morph.join('_'))
                )
            )
        )
    });
};
var get_checked_rules = function(category_seq){
    var words = [];
    $('input:checkbox[name=word-selection]:checked').each(function(){
        var tmp = $(this).val().split('_');
        var seq = tmp[0];
        var word = tmp.slice(1).join('_');
        words.push({'word': word, 'seq': seq});
    });
    return words;
};
var uncheck_checkboxes = function(){
    $('input:checkbox[name=word-selection]:checked').removeAttr('checked');
};
var empty_checkboxes = function(){
    $('#rule-checkboxes').empty();
};

var show_sentences = function(post_id, title, sentences){
    $('#post-modal-body-p').empty();
    $('#post-modal-header-h4').text(title);
    $.each(sentences, function(){
        var sentence_id = this.sentence_id;
        var full_text = this.full_text;
        $('#post-modal-body-p').append(
            $('<span>').attr({
                'class':'sentence',
                'id':'sentence-span-'+sentence_id,
                'name':'sentence-span',
            }).text(full_text)
        );
        var rules = this.rules;
        if(rules.length != 0){
            var color = colors[rules[0]%(colors.length)];
            $('#sentence-span-'+sentence_id).css('background-color', convertHex(color, 50));
            $('#sentence-span-'+sentence_id).attr({
                'data-toggle':'popover',
                'rules':rules
            })
        }
    });
    $(document).on({
        'mouseenter': function(e){
            var popover = '#sentence-detail-popover';
            var rules = this.getAttribute('rules').split(',');
            for(var i=0; i<rules.length; i++){
                var rule_id = rules[i];
                var category_seq = get_ruleset_by_rule(rule_id);
                var ruleset = $('#ruleset-a-'+category_seq)[0].text;
                var rule_title = $('#rule-div-'+rule_id)[0].getAttribute('data-original-title');
                var rule_words = $('span[name=rule-span-word-'+rule_id+']');
                var rule_words_html = ''
                for(var j=0; j<rule_words.length; j++){
                    rule_words_html += rule_words[j].outerHTML
                }
                $('#sentence-detail-popover-tbody').append(
                    $('<tr>').append(
                        $('<td>').text(ruleset),
                        $('<td>').text(rule_title),
                        $('<td>').append(rule_words_html)
                    )
                )
            }
            $(popover).show();
        },
        'mouseleave': function () {
            var popover = '#sentence-detail-popover';
            if (!($(this).hasClass("show"))) {
                $(popover).hide();
                $(popover+'-tbody').empty();
            }
        }
    }, 'span[data-toggle="popover"]'
    );
    $(document).on('mousemove', 'span[data-toggle="popover"]', function(e){
        var popover = '#sentence-detail-popover';
        var leftD = e.pageX + 20;
        topD = e.pageY - ($(popover).outerHeight() + 20);
        $(popover).css('top', topD).css('left', leftD);
    });
};


var show_posts = function(posts){
    $.each(posts, function(){
        $('#posts').append(
                $('<tr>').prepend(
                $('<td>').append(
                    $('<a>').attr({
                        'name':'post-a',
                        'id':'poast-a-'+this.id,
                        'value': this.id,
                        'data-toggle':'modal',
                        'data-target':'#post-modal'
                    }).text(this.title)
                ),
                $('<td>').text(this.url)
            )
        );
    });
    $(document).on('click', 'a[name=post-a]', function(){
        var post_id = this.getAttribute('value');
        var title = this.text;
        jQuery.ajax({
            type: 'GET',
            url: '/_sentences',
            data: {
                'topic': topic,
                'sources':JSON.stringify(sources),
                'post_id': post_id
            },
            dataType: 'JSON',
            success: function(data){
                show_sentences(post_id, title, data.sentences);
            },
            error: function(xhr, status, error){
                console.log('get sentences failed');
            }
        });
    });
};

var show_rules = function(ruleset_rules_dic, rule_count_dic){
    for(var category_seq in ruleset_rules_dic){
        rules = ruleset_rules_dic[category_seq];
        $.each(rules, function(){
            var rule_id= this.rule_id;
            var full_text = this.full_text;
            var words = this.word;
            $('#ruleset-menu-'+category_seq).append(
                $('<li>').attr({
                    'id':'rule-li-'+rule_id
                }).append(
                    $('<a>').append(
                    $('<div>').attr({
                        'class':'clearfix rules',
                        'id':'rule-div-'+rule_id,
                        'data-toggle':'tooltip',
                        'data-replacement':'top',
                        'title':full_text
                    }).append(
                        $('<span>').attr({'class':'pull-right'}).append(
                            $('<span>').attr({
                                'class':'badge',
                                'id':'rule-badge-'+rule_id,
                                'name':'rule-badge-'+category_seq,
                                'style':'margin-right:5px'
                            }),
                            $('<button>').attr({
                                'class':'btn btn-warning btn-xs glyphicon glyphicon-remove ruleset-button',
                                'value':rule_id,
                                'name':'delete-rule-btn'
                            })
                        )
                    )
                    )
                )
            );
            $.each(words, function(){
                $('#rule-div-'+rule_id).append(
                    $('<span>').attr({
                        'class':'label label-default',
                        'name':'rule-span-word-'+rule_id,
                        'style':'margin:3px'
                    }).text(this)
                )
            });
        });
    }
    update_rule_badge(rule_count_dic);
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
                var category_seq = get_ruleset_by_rule(rule_id);
                var rule_count = parseInt($('#rule-badge-'+rule_id)[0].textContent);
                var ruleset_badge = $('#ruleset-badge-'+category_seq)[0];
                var current_count = parseInt(ruleset_badge.textContent);
                ruleset_badge.textContent = current_count - rule_count;
                $('#rule-li-'+rule_id).remove()
            },
            error: function(xhr, status, error){
                console.log('get rules failed');
            }
        });
    });
    $(function(){
        $('[data-toggle="tooltip"]').tooltip();
    });
}

var update_rule_badge = function(rule_count_dic){
    for(var rule_id in rule_count_dic){
        $('#rule-badge-'+rule_id.toString())[0].innerHTML = rule_count_dic[rule_id];
    }
    var ruleset_badges = $('span[name=ruleset-badge]');
    for(var i=0; i<ruleset_badges.length; i++){
        ruleset_badge = ruleset_badges[i];
        var sum = 0;
        var category_seq = ruleset_badge.id.split('-').pop();
        var rule_badges = $('span[name=rule-badge-'+category_seq+']');
        for(var j=0; j<rule_badges.length; j++){
            rule_badge = rule_badges[j]
            sum += parseInt(rule_badge.innerHTML)
        }
        if(isNaN(sum)){
            ruleset_badge.innerHTML = ''
        }else{
            ruleset_badge.innerHTML = sum
        }
    }
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
                        $('<span>').attr({
                            'class':'badge',
                            'id':'ruleset-badge-'+category_seq,
                            'name':'ruleset-badge',
                            'style':'margin-right:5px'
                        }),
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
        //jQuery.ajax({
            //type: 'GET',
            //url: '/_rules',
            //data: {
                //'topic': topic,
                //'category_seq': category_seq 
            //},
            //dataType: 'JSON',
            //success: function(data){
                //show_rules(category_seq, data.rules, data.rule_count_dic);
            //},
            //error: function(xhr, status, error){
                //console.log('get rules failed');
            //}
        //});
    });
    //$(document).on('click', 'a[name=ruleset-a]', function(){
        //if(ishover){return}
        //var category_seq = this.getAttribute('value');
        //jQuery.ajax({
            //type: 'GET',
            //url: '/_rules',
            //data: {
                //'topic': topic,
                //'category_seq': category_seq 
            //},
            //dataType: 'JSON',
            //success: function(data){
                //show_rules(category_seq, data.rules)
            //},
            //error: function(xhr, status, error){
                //console.log('get rules failed');
            //}
        //});
    //});

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
            'mouseenter': function(){ ishover = true; },
            'mouseleave': function(){ ishover = false; }
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
                show_rules(data.ruleset_rules_dic, data.rule_count_dic);
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
        var checked = get_checked_rules();
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
                var ruleset_rules_dic = {}
                ruleset_rules_dic[category_seq] = data.rules
                show_rules(ruleset_rules_dic);
            },
            error: function(xhr, status, error){
                console.log('rule is not posted');
            }
        });
        uncheck_checkboxes();
    });

    $('#run').click(function(){
        jQuery.ajax({
            type: 'POST',
            url: '/_analysis',
            data: {
                'topic': JSON.stringify(topic),
                'sources': JSON.stringify(sources)
            },
            dataType: 'JSON',
            success: function(data){
                update_rule_badge(data.rule_count_dic);
            },
            error: function(xhr, status, error){
                console.log('run fail');
            }
        });
    });
};

$(document).ready(main);

