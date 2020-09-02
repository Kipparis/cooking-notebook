#!sh

# -k - используем iconv
# -ms - используем макро ms (man groff_ms)
groff -k -T utf8 -ms plan.ms | less
