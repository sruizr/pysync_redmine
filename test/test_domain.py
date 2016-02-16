from pysync_redmine.domain import (
                                   Repository,
                                   Project,
                                   Task,
                                   RelationSet,
                                   Phase,
                                   Member,
                                   StringTree)
import pdb


class A_StringTree:

    def should_init_without_parent(self):
        tree = StringTree()

        assert tree.name == '/'
        assert tree.parent is None

    def should_init_with_string_name(self):
        root = StringTree('root')
        node = StringTree('node 1', root)

        assert node.name == 'node 1'
        assert root == node.parent
        assert len(root.childs) == 1
        assert node in root.childs

    def should_init_with_path(self):
        root = StringTree('root')

        name = ['node 1', 'node 2']

        node = StringTree(name, root)

        assert node.name == 'node 2'
        assert node.parent.name == 'node 1'
        assert node.parent.parent == root
        assert node in node.parent.childs
        assert node.parent in root.childs

    def should_give_path(self):
        root = StringTree('root')

        name = ['node 1', 'node 2']

        node = StringTree(name, root)

        assert node.path(root) == ['node 1', 'node 2']
        assert node.path() == ['root', 'node 1', 'node 2']
        assert node.path(node) == []
        assert node.path(node.parent) == ['node 2']

    def should_find_childs_by_name(self):
        root = StringTree('root')

        name_11 = ['node 1', 'node 11']
        name_21 = ['node 2', 'node 21']

        node_11 = StringTree(name_11, root)
        node_21 = StringTree(name_21, root)

        assert node_11.parent == root.find('node 1')
        assert node_11.parent.find('node 11') == node_11
        assert node_21.parent == root.find('node 2')

    def should_add_node(self):
        root = StringTree('root')

        node = root.add_node(['node 1', 'node 1.0', 'node 1.0.0'])

        assert len(root.childs) == 1
        assert len(root.find('node 1').childs) == 1
        assert len(root.find('node 1').find('node 1.0').childs) == 1
        assert node.path() == ['root', 'node 1', 'node 1.0', 'node 1.0.0']

    def should_add_node_without_duplicates(self):
        root = StringTree('root')
        node = root.add_node(['1', '2'])
        same_node = root.add_node(['1', '2'])
        new_node = root.add_node(['1', '2', '3'])

        assert node == same_node
        assert len(root.childs) == 1
        assert new_node.parent == node
        assert new_node.path() == ['root', '1', '2', '3']
