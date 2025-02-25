import hashlib
import json
from bs4 import BeautifulSoup

class Node:
    def __init__(self, tag, attributes=None, content=None):
        self.tag = tag
        self.attributes = attributes if attributes else {}
        self.content = content
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def to_dict(self):
        return {
            'tag': self.tag,
            'attributes': self.attributes,
            'content': self.content,
            'children': [child.to_dict() for child in self.children]
        }

    def compute_hash(self):
        hasher = hashlib.sha256()
        hasher.update(self.tag.encode('utf-8'))
        for attr, value in sorted(self.attributes.items()):
            hasher.update(attr.encode('utf-8'))
            hasher.update(str(value).encode('utf-8'))
        if self.content:
            hasher.update(self.content.encode('utf-8'))
        for child in self.children:
            hasher.update(child.compute_hash().encode('utf-8'))
        return hasher.hexdigest()

def parse_html_to_tree(html):
    soup = BeautifulSoup(html, 'html.parser')


    html_element = soup.find("html")  
    if not html_element:
        raise ValueError("No <html> tag found in the document")

    return build_tree(html_element)

def build_tree(soup_element):
    if isinstance(soup_element, str):
        if soup_element.strip():  
            return Node(tag='text', content=soup_element.strip())
        return None  
    
    if soup_element.name in ["script", "style"]:
        return None  

    node = Node(tag=soup_element.name, attributes=soup_element.attrs)

    for child in soup_element.children:
        child_node = build_tree(child)
        if child_node:  
            node.add_child(child_node)

    return node

def compare_trees(node1, node2, path="root"):
    differences = []

    if node1 is None and node2 is not None:
        differences.append(f"{path}: Node missing in first tree")
        return differences
    elif node1 is not None and node2 is None:
        differences.append(f"{path}: Node missing in second tree")
        return differences

    if node1.tag != node2.tag:
        differences.append(f"{path}: Tag mismatch ({node1.tag} != {node2.tag})")

    if node1.attributes != node2.attributes:
        differences.append(f"{path}: Attribute mismatch ({node1.attributes} != {node2.attributes})")

    if node1.content != node2.content:
        differences.append(f"{path}: Text content mismatch ({node1.content} != {node2.content})")

    if len(node1.children) != len(node2.children):
        differences.append(f"{path}: Number of children differ ({len(node1.children)} != {len(node2.children)})")

    for i, (child1, child2) in enumerate(zip(node1.children, node2.children)):
        child_path = f"{path} > {node1.tag}[{i}]"
        differences.extend(compare_trees(child1, child2, path=child_path))

    if len(node1.children) > len(node2.children):
        for i in range(len(node2.children), len(node1.children)):
            differences.append(f"{path} > {node1.tag}[{i}]: Extra node in first tree")
    elif len(node2.children) > len(node1.children):
        for i in range(len(node1.children), len(node2.children)):
            differences.append(f"{path} > {node2.tag}[{i}]: Extra node in second tree")

    return differences


if __name__ == "__main__":
    try:
        with open("dom1.html", "r", encoding="utf-8") as file1, \
            open("dom2.html", "r", encoding="utf-8") as file2:
            html1 = file1.read()
            html2 = file2.read()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)

    tree1 = parse_html_to_tree(html1)
    tree2 = parse_html_to_tree(html2)

    hash1 = tree1.compute_hash()
    hash2 = tree2.compute_hash()

    differences = compare_trees(tree1, tree2)

    output = {
        'tree1': tree1.to_dict(),
        'tree2': tree2.to_dict(),
        'comparison': differences
    }

    output_file = "output.json"  
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)  

    print(f"Output saved to {output_file}")
