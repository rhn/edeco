// A test for nested loops structurizing
// Uses x86_64 assembly

// nontrivial splitting, all nodes present
//     1
//     /^
//   2/  ^
//   ^\  ^ 
//  ^  \^  
//  ^  /3
//   ^/   
//    4  
//    | 
//    5
00 <test>:
    0:  00      nop // 0
    1:  01      nop // 1
    2:  02      nop // 1
    3:  03      nop // 2
    4:  03      jne 1 // 3
    5:  04      nop // 4
    6:  04      jne 3 // 4
    7:  05      ret // 5


// Structure (numbers are sections):
// function test {
//    0
//    flow looplike {{
//        -> #0
//        #0 {
//            1
//        } -> #1
//        #1 {
//            2
//            3
//        } -> #0, #2
//        #2 {
//            4
//        } -> #1, end
//    }} looplike
//    5
//}
