drop table if exists sentence_word_relations;
drop table if exists rule_word_relations;
drop table if exists rules;
drop table if exists rulesets;
drop table if exists words;
drop table if exists sentences;
drop table if exists posts;
drop table if exists topics;
drop table if exists sources;

/* [static] topic of an analysis */
CREATE TABLE topics(
    _id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) CHARACTER SET UTF8MB4
);

/* [static] We will use only few sources. Twitter / Instagram / YouTube / NewsInWeb. */
CREATE TABLE sources(
    _id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) CHARACTER SET UTF8MB4
);

/* vocab */
CREATE TABLE words(
    _id INT PRIMARY KEY AUTO_INCREMENT,
    word VARCHAR(128) CHARACTER SET UTF8MB4,
    UNIQUE KEY `idx_word` (`word`) USING HASH
);

/* each post in a topic, crawled from one of the sources */
CREATE TABLE posts(
    _id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT,
    source_id INT,
    title VARCHAR(255) CHARACTER SET UTF8MB4,
    url TEXT CHARACTER SET UTF8MB4,
    FOREIGN KEY (topic_id) REFERENCES topics(_id),
    FOREIGN KEY (source_id) REFERENCES sources(_id)
);

/* each sentence in a post. Since sentence is the base unit for grading the rules, we decided to create this table */
CREATE TABLE sentences(
    post_id INT,
    sentence_seq INT,
    full_text TEXT CHARACTER SET UTF8MB4,
    PRIMARY KEY (post_id, sentence_seq),
    FOREIGN KEY (post_id) REFERENCES posts(_id)
);

/* store the word orders */
CREATE TABLE sentence_word_relations(
    post_id INT,
    sentence_seq INT,
    word_seq INT,
    word_id INT,
    PRIMARY KEY (post_id, sentence_seq, word_seq),
    FOREIGN KEY (post_id, sentence_seq) REFERENCES sentences(post_id, sentence_seq),
    FOREIGN KEY (word_id) REFERENCES words(_id)
);

/* [static] each topic has 4~6 rulesets. (most of them has 5 categories) */
CREATE TABLE rulesets(
    topic_id INT,
    category_seq INT,   /* since it would be weird to see '103th ruleset' in screen, I changed this to 'category_number' */
    name VARCHAR(255) CHARACTER SET UTF8MB4,
    PRIMARY KEY (topic_id, category_seq),
    FOREIGN KEY (topic_id) REFERENCES topics(_id)
);

/* each rules in a ruleset */
CREATE TABLE rules(
    _id INT PRIMARY KEY AUTO_INCREMENT,
    topic_id INT,
    category_seq INT,
    full_text TEXT CHARACTER SET UTF8MB4,
    INDEX `idx_topicid_categoryseq` (`topic_id` ASC, `category_seq` ASC),
    FOREIGN KEY (topic_id, category_seq) REFERENCES rulesets(topic_id, category_seq)
);

/* store the word orders */
CREATE TABLE rule_word_relations(
    rule_id INT,
    word_seq INT,
    word_id INT,
    PRIMARY KEY (rule_id, word_seq),
    FOREIGN KEY (rule_id) REFERENCES rules(_id),
    FOREIGN KEY (word_id) REFERENCES words(_id)
);
