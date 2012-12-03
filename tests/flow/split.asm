// A bunch of tests for splitting
// Uses x86_64 assembly

// nontrivial splitting, all nodes present
//   1
//   /\
// 2/  \ 3
//  \  /\
//   \/  \ 5
//  4 \  /
//     \/
//      6

00 <test>:
    0:  00      nop // 0
    1:  01      jne 5 // 1
    2:  02      nop // 2
    3:  04      nop // 4
    4:  04      jmp 8 // 4
    5:  03      nop // 3
    6:  03      jne 3 // 3
    7:  05      nop // 5
    8:  06      nop // 6
    9:  06      ret // 6
