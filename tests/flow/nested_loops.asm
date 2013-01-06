// A test for nested loops structurizing
// Uses x86_64 assembly

// nontrivial splitting, all nodes present
//     1
//     /^
//    /  ^
//  2/^   ^
//  /  ^   ^
//  \  ^   ^
//   \^   ^
//   3\  ^
//     \^
//      4
//      |
//      5
00 <test>:
    0:  00      nop // 0
    1:  01      nop // 1
    2:  02      nop // 2
    3:  03      nop // 3
    4:  03      jne 2 // 3
    5:  04      nop // 4
    6:  04      jne 1 // 4
    9:  05      ret // 5
