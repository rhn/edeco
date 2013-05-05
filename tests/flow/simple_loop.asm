// A bunch of tests for reverse flows
// Uses x86_64 assembly

// nontrivial end, all nodes present
//     1
//     /X
//    /  X
//   2\  X
//     \X
//      3
//      |4

00 <test>:
    0:  00      nop // 0
    1:  01      nop // 1
    2:  02      nop // 2
    3:  03      nop // 3
    4:  03      jne 1 // 3
    5:  04      nop // 4
    6:  04      ret // 4
