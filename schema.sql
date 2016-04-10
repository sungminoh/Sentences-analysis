drop table if exists sentence_word_relations;
drop table if exists rule_word_relations;
drop table if exists rules;
drop table if exists rulesets;
drop table if exists words;
drop table if exists sentences;
drop table if exists posts;

create table posts(
    _id int primary key auto_increment,
    url varchar(255) character set utf8mb4,
    title varchar(255) character set utf8mb4
);
create table words(
    _id int primary key auto_increment,
    word varchar(255) character set utf8mb4
);
create table rulesets(
    _id int primary key auto_increment,
    name varchar(255) character set utf8mb4
);

create table rules(
    _id int primary key auto_increment,
    ruleset_id int,
    full_text text character set utf8mb4,
    foreign key (ruleset_id) references rulesets(_id)
);
create table sentences(
    post_id int,
    sentence_seq int,
    full_text text character set utf8mb4,
    primary key (post_id, sentence_seq),
    foreign key (post_id) references posts(_id)
);
create table sentence_word_relations(
    post_id int,
    sentence_seq int,
    word_seq int,
    word_id int,
    primary key (post_id, sentence_seq, word_seq),
    foreign key (post_id, sentence_seq) references sentences(post_id, sentence_seq),
    foreign key (word_id) references words(_id)
);
create table rule_word_relations(
    rule_id int,
    word_seq int,
    word_id int,
    primary key (rule_id, word_seq),
    foreign key (rule_id) references rules(_id),
    foreign key (word_id) references words(_id)
);
