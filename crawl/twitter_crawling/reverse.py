import os
import re

dirname = './posts'
dirdest = './reversed'
pattern = '\[[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\]'

for filename in os.listdir(dirname):
    source = os.path.join(dirname, filename)
    splited = filename.strip().split(' ')
    filename = ' '.join([splited[i] for i in [3, 4, 2, 0, 1, 5]])
    result = os.path.join(dirdest, filename)
    f = open(source)
    fr = open(result, 'w')

    posts = []
    post = []
    started = False
    for line in f:
        line = line.strip() + '\n'
        if re.match(pattern, line):
            started = True
            if post:
                posts.append(''.join(post))
                del post[:]
        if not started:
            if len(line) > 10:
                splited = line.strip().split(' ')
                line = ' '.join([splited[i] for i in [3, 4, 2, 0, 1, 5]]) + '\n'
            fr.write(line)
        else:
            post.append(line)

    if post:
        posts.append(''.join(post))
        del post[:]

    posts.reverse()
    fr.write(''.join(posts))
    del posts[:]
