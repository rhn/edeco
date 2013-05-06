// A bunch of tests for splitting
// Uses x86_64 assembly

// trivial splitting, all nodes present
//   1
//   /\
// 2/  \
//  \  /
//   \/
//   3

00 <test>:
    0:  00      nop // 0
    1:  01      jne 3 // 1 -> 3
    2:  02      nop // 2
    3:  03      nop // 3
    4:  03      ret // 3
