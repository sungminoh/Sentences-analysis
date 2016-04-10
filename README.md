# Korean SNS & Article Analysis

## Back-end

### Crawling

**Todo**

1. Crawl Naver news or Google news based on a query
2. Connect to the parsing part to parse and store in database automatically

_ _ _

### Parsing using KoNLPy
**Todo**

1. Store the morphemes and sentence information into the database

**Issue**

1. Are all the morphems indeed needed? (ex. 의, 는, 이다, etc.)
2. Multi threading in parsing process doesn't work. It works only for short sentences.

**Done**

*2016.04.09.*

1. Used dummy text file
2. Parsed each line to sentences with multi threading process (2 threads)
3. ~~Parsed each sentences to morphemes with multi threading process (2 threads)~~ doesn't work.

_ _ _

### REST API

**Todo**

| API | Description | CRUD |
|--------|--------|--------|
| (topics) GET <br> /topics/ | <ul><li>Get all topics from the database.</li></ul> | <strong>R</strong><ul><li>topics</li></ul> |
| (sources) GET <br> /sources/ | <ul><li>Get all sources from the database.</li></ul> | <strong>R</strong><ul><li>sources</li></ul> |
| (rulesets) POST <br> /rulesets/{topic_id}/{ruleset_seq}/{name} | <ul><li>Create new ruleset.</li><li>Which is a kind of package of rules.</li></ul> | <strong>C</strong><ul><li>rulesets</li></ul> |
| (rulesets) GET <br> /rulesets/{topic_id} | <ul><li>Get all the rulesets from the database.</li></ul> | <strong>R</strong><ul><li>rulesets</li></ul> |
| (rulesets) PUT <br> /rulesets/{topic_id}/{ruleset_seq}/{new_name} | <ul><li>Change the name of the ruleset.</li></ul> | <strong>U</strong><ul><li>rulesets</li></ul> |
| (rulesets) DELETE <br> /rulesets/{topic_id}/{ruleset_seq} | <ul><li>Delete the ruleset and its realted rules.</li></ul> | <strong>D</strong><ul><li>rulesets</li><li>rules</li><li>rule_word_relations</li></ul> |
| (words) POST <br> /words/{fulltext} | <ul><li>Parse the {fulltext} into morphemes.</li><li>Store the unregistered morphems into words table.</li><li>Get morphemes of the fulltext after parsing.</ul> | <strong>C</strong><ul><li>words</li></ul> |
| (rules) POST <br> /rules/{topic_id}/{ruleset_seq}/{fulltext}/{word_ids} | <ul><li>Create an actual rule, combination of words.</li></ul> | <strong>C</strong><ul><li>rules</li><li>rule_word_relations</li></ul> |
| (rules) GET <br> /rules/{topic_id}/{ruleset_seq} | <ul><li>Get rules of the selected rulset.</li></ul> | <strong>R</strong><ul><li>rules</li><li>(rule_word_relations?)</li></ul> |
| (rules) GET <br> /rules/{rule_id} | <ul><li>Get specific rule.</li></ul> | <strong>R</strong><ul><li>rules</li><li>rule_word_relations</li></ul> |
| (rules) PUT <br> /rules/{rule_id}/{word_ids} | <ul><li>Change the rule, combination of words.</li></ul> | <strong>U</strong><ul><li>rule_word_relations</li></ul> |
| (rules) DELETE <br> /rules/{rule_id} | <ul><li>Delete the rule, either fulltext and combination of words.</li></ul> | <strong>D</strong><ul><li>rules</li><li>rule_word_relations</li></ul> |




**Issue**

1. See Database - Issue 2.

**Done**

_ _ _

### Database

**Todo**

**Issue**

1. Some emojis are not properly saved. Some are saved just like '?????'
2. How about create 'querys' table to store the queries which are used to crawl the posts. (ex. 총선)
	Then it is possible to categorize the posts and user can analyze only the posts they are interested in.
    If we only want to analyze just all of the recent posts, it might be redundant data.
    However, still it is a good option, considering expandability.

**Done**

*2016.04.09.*
1. Created database shceme and initializing code.

* * *

## Front-end

**Todo**

**Issue**

**Done**
