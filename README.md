# Korean SNS & Article Analysis

## Back-end
### Crawling
** Todo **
1. Crawl Naver news or Google news based on a query
2. Connect to the parsing part to parse and store in database automatically

_ _ _

### Parsing using KoNLPy
** Todo **
1. Store the morphemes and sentence information into the database

** Issue **
1. Are all the morphems indeed needed? (ex. 의, 는, 이다, etc.)

** Done **
*2016.04.09.*
1. Used dummy text file
2. Parsed each line to sentences with multi threading process (2 threads)
3. Parsed each sentences to morphemes with multi threading process (2 threads)

_ _ _

### REST API
** Todo **

** Issue **

** Done **

_ _ _

### Database
** Todo **

** Issue **
1. Some emojis are not properly saved. Some are saved just like '?????'

** Done **
*2016.04.09.*
1. Created database shceme and initializing code.

_ _ _

## Front-end
** Todo **

** Issue **

** Done **