drop table if exists sentence_word_relations;
drop table if exists rule_word_relations;
drop table if exists rules;
drop table if exists rulesets;
drop table if exists words;
drop table if exists sentences;
drop table if exists posts;

create table posts(
    post_id int primary key auto_increment,
    author varchar(255) character set utf8mb4,
    url varchar(255) character set utf8mb4,
    title varchar(255) character set utf8mb4
);
create table sentences(
    sentence_id int primary key auto_increment,
    post_id int,
    sentence_seq int,
    content text character set utf8mb4,
    foreign key (post_id) references posts(post_id)
);
create table words(
    word_id int primary key auto_increment,
    word varchar(255) character set utf8mb4
);
create table rulesets(
    ruleset_id int primary key auto_increment,
    name varchar(255) character set utf8mb4
);
create table rules(
    rule_id int primary key auto_increment,
    ruleset_id int,
    foreign key (ruleset_id) references rulesets(ruleset_id)
);
create table sentence_word_relations(
    sentence_id int,
    word_id int,
    word_seq int,
    foreign key (sentence_id) references sentences(sentence_id),
    foreign key (word_id) references words(word_id)
);
create table rule_word_relations(
    rule_id int,
    word_id int,
    foreign key (rule_id) references rules(rule_id),
    foreign key (word_id) references words(word_id)
);
