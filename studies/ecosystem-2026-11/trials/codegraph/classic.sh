#!/bin/sh
# Ask classic C tools the five questions in truth.json. Run inside the classic image
# with the fixture copied to a writable /work (index files are written there).
cd /work
echo "### versions"; cat /versions.txt
echo "### ctags: is handle_uart defined (Q5)?"
ctags -R -x --c-kinds=f src | grep -E "handle_|submit" || echo "(no handle_ or submit definitions)"
echo "### cscope"
cscope -bk -Iinclude src/*.c include/*.h
echo "-- Q1 functions calling dev_open"; cscope -dL -3 dev_open
echo "-- Q2 functions called by dev_open"; cscope -dL -2 dev_open
echo "-- Q3 functions called by timer_fire"; cscope -dL -2 timer_fire
echo "-- Q4 functions called by submit"; cscope -dL -2 submit
echo "-- Q5 definition of handle_uart"; cscope -dL -1 handle_uart
echo "### GNU Global"
gtags
echo "-- Q5 definition of handle_uart"; global -x handle_uart || echo "(none)"
echo "-- Q1 references to dev_open"; global -rx dev_open
echo "### cflow with the preprocessor"
echo "-- Q1 reverse tree for dev_open"; cflow --cpp="cc -E -Iinclude" -r src/*.c | grep -A3 "^dev_open"
echo "-- Q2-Q4 forward tree from main"; cflow --cpp="cc -E -Iinclude" -m main src/*.c
echo "### clang call graph dump"
for f in src/*.c; do clang --analyze -Xclang -analyzer-checker=debug.DumpCallGraph -Iinclude "$f" -o /dev/null 2>&1 | grep -E "Function: (main|dev_open|dev_close|timer_fire|submit|handle_uart|handle_spi) "; done
