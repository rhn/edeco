// A bunch of tests for splitting
// Uses x86_64 assembly

// trivial splitting, all nodes present
//   1
//   /\
// 2/  \3
//  \  /
//   \/
//   4

00 <test>:
    0:  00      nop // 0
    1:  01      jne 4 // 1 -> 3
    2:  02      nop // 2
    3:  02      jmp 5 // 2 -> 4
    4:  03      nop // 3
    5:  04      nop // 4
    6:  04      ret // 4
