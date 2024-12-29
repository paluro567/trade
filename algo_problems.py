'''
Two Sum: Given an array of integers, return indices of the two numbers such that they add up to a specific target.
'''
def two_sum(nums, target):
    # Dictionary to store the complement and its index
    num_map = {}
    
    # Iterate through the array
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    
    # If no solution exists (though the problem assumes one always does)
    return []

# Example Usage
def solution1():
    print("expecting [0, 3]")
    nums = [2,  11, 15, 7,]
    target = 9
    result = two_sum(nums, target)
    print("Indices:", result)  

# solution1()



'''
Longest Substring Without Repeating Characters: Find the length of the longest substring without repeating characters.
'''

def length_of_longest_substring(s):
    # Dictionary to store the index of characters
    char_index_map = {}
    # Initialize pointers and max length
    left = 0
    max_length = 0

    # Iterate through the string
    for right in range(len(s)):
        char = s[right]
        # If the character is already in the map and its index is within the current window
        if char in char_index_map and char_index_map[char] >= left:
            # Move the left pointer to the right of the duplicate character
            left = char_index_map[char] + 1
        
        # Update the character's index in the map
        char_index_map[char] = right
        
        # Calculate the length of the current window
        current_length = right - left + 1
        # Update the maximum length if the current window is longer
        max_length = max(max_length, current_length)
    
    return max_length

def solution2():
    print("expecting 3")
    s = "abcabcbb"
    result = length_of_longest_substring(s)
    print("Length of the longest substring without repeating characters:", result)  

# solution2()


class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    # Function to append a new node to the end of the list
    def append(self, value):
        new_node = Node(value)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    # Function to reverse the linked list in place
    def reverse(self):
        prev = None
        current = self.head
        while current:
            next_node = current.next  # Save the next node
            current.next = prev       # Reverse the link
            prev = current            # Move prev to current
            current = next_node       # Move current to next node
        self.head = prev  # Update the head to the new start of the list

    # Function to print the linked list
    def print_list(self):
        current = self.head
        while current:
            print(current.value, end=" -> ")
            current = current.next
        print("None")

def solution3():

    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.append(4)

    print("Original Linked List:")
    ll.print_list()

    ll.reverse()

    print("Reversed Linked List:")
    ll.print_list()


# solution3()









'''
1. Arrays and Strings
Two Sum: Given an array of integers, return indices of the two numbers such that they add up to a specific target.
Longest Substring Without Repeating Characters: Find the length of the longest substring without repeating characters.
Rotate Array: Rotate an array by k steps.
Merge Sorted Arrays: Merge two sorted arrays into one sorted array.
2. Linked Lists
Reverse a Linked List: Reverse a singly linked list in place.
Detect Cycle in a Linked List: Use Floyd's Cycle Detection Algorithm.
Merge Two Sorted Linked Lists: Merge two sorted linked lists into one.
Remove Nth Node From End of List: Remove the nth node from the end of a singly linked list.
3. Trees
Binary Tree Inorder Traversal: Perform an in-order traversal of a binary tree.
Maximum Depth of Binary Tree: Find the maximum depth of a binary tree.
Lowest Common Ancestor: Find the lowest common ancestor of two nodes in a binary tree.
Validate Binary Search Tree: Check if a binary tree is a valid BST.
4. Searching and Sorting
Binary Search: Implement binary search on a sorted array.
Kth Largest Element in an Array: Find the kth largest element in an array.
Merge Intervals: Merge overlapping intervals.
Quick Sort or Merge Sort: Explain and implement one of these algorithms.
5. Recursion and Backtracking
Generate Parentheses: Generate all combinations of well-formed parentheses.
Permutations and Combinations: Find all permutations or combinations of an array.
Sudoku Solver: Solve a Sudoku puzzle using backtracking.
Word Search: Find if a word exists in a grid of letters.
6. Dynamic Programming
Climbing Stairs: Find the number of ways to climb a staircase with n steps.
Longest Common Subsequence: Find the longest subsequence present in two sequences.
Knapsack Problem: Solve the 0/1 Knapsack Problem.
Coin Change Problem: Find the minimum number of coins needed to make a target sum.
7. Graphs
Depth-First Search (DFS): Implement DFS for a graph.
Breadth-First Search (BFS): Implement BFS for a graph.
Detect Cycle in a Graph: Check if a cycle exists in a directed or undirected graph.
Shortest Path: Implement Dijkstra's or BFS for finding the shortest path.
8. Stacks and Queues
Valid Parentheses: Check if a string of parentheses is valid.
Implement Queue Using Stacks: Use two stacks to implement a queue.
Min Stack: Design a stack that supports push, pop, and retrieving the minimum element in constant time.
Sliding Window Maximum: Find the maximum in every sliding window of size k.
9. Bit Manipulation
Single Number: Find the element that appears only once in an array where every other element appears twice.
Number of 1 Bits: Count the number of 1 bits in an integer.
Power of Two: Determine if an integer is a power of two.
XOR Problems: Use XOR to solve missing or duplicate number problems.
10. Math
FizzBuzz: Print numbers from 1 to n with special rules.
Reverse Integer: Reverse digits of an integer.
Greatest Common Divisor (GCD): Calculate the GCD of two numbers.
'''


class node2:
    def __init__(self, value):
        self.value = value
        self.next = None

class linkedl2:
    def __init__(self):
        self.head = None
    def print_ll(self):
        list_str=""
        head=self.head
        while head:
            list_str+=str(head.value)+"->"
            head=head.next
        list_str+="None"
        print(list_str)
        return

    def append(self,value):
        if not self.head:
            self.head=node2(value)
            print("added: ", value)
            return
        end=self.head
        while end.next!=None:
            end=end.next
        end.next=node2(value)
        print("added: ", value)
        return
    


    def reverse(self):
        prev=None
        cur=self.head
        while cur:
            nn=cur.next
            cur.next=prev
            prev=cur
            cur=nn
        self.head = prev


    def remove_nth_from_end(self, n):
        # Create a dummy node to simplify edge cases
        dummy = Node(0)
        dummy.next = self.head
        first = dummy
        second = dummy

        # Move first pointer n+1 steps ahead
        for _ in range(n + 1):
            if first:
                first = first.next

        # Move both pointers until first reaches the end
        while first:
            first = first.next
            second = second.next

        # Remove the nth node
        second.next = second.next.next

        # Update the head in case the head node was removed
        self.head = dummy.next
    
def trial():
    ll_inst=linkedl2()
    ll_inst.append(1)
    ll_inst.append(2)
    ll_inst.append(3)
    ll_inst.append(4)

    ll_inst.print_ll()
    ll_inst.reverse()
    ll_inst.print_ll()

# trial()
    
def trial3():
    ll = linkedl2()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.append(4)
    ll.append(5)
    print("Original Linked List:")
    ll.print_ll()

    ll.remove_nth_from_end(2)

    print("After Removing 2nd Node from End:")
    ll.print_ll()

# trial3()






# max depth binary search tree

class TreeNode:
    def __init__(self, value=0, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def max_depth(root):
    if not root:
        return 0
    left_depth = max_depth(root.left)
    right_depth = max_depth(root.right)
    return 1 + max(left_depth, right_depth)

# Example Usage:
# Binary Tree:
#         1
#        / \
#       2   3
#      / \
#     4   5
def solution4():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)

    print("Maximum Depth:", max_depth(root))  # Output: 3

solution4()









        


    

