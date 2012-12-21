// A bunch of tests for reverse flows
// Uses x86_64 assembly

// nontrivial splitting, all nodes present
//     1
//     /X
//    /  X
//  2/\  X
//  /  \X
// 3\  / 4
//   \/
//    5

00 <test>:
    0:  00      nop // 0
    1:  01      nop // 1
    2:  02      nop // 2
    3:  02      jne 6 // 2
    4:  03      nop // 3
    5:  03      jmp 8 // 3
    6:  04      nop // 4
    7:  04      jne 1 // 4
    8:  06      nop // 5
    9:  06      ret // 5
