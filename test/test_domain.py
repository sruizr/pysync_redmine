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

    def should_init_with_parent(self):
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

    def should_insert_node_into_right_place(self):
        root = StringTree('root')

        node1 = StringTree(['node 1', 'node 1.0', 'node 1.0.0'], root)
        node2 = StringTree(['node 1', 'node 1.1'], root)
        node3 = StringTree(['node 1', 'node 1.0', 'node 1.0.1'], root)

        assert len(root.childs) == 1
        assert len(root.find('node 1').childs) == 2
        assert len(root.find('node 1').find('node 1.0').childs) == 2
        assert node1.path() == ['root', 'node 1', 'node 1.0', 'node 1.0.0']
        assert node2.path() == ['root', 'node 1', 'node 1.1']
        assert node3.path() == ['root', 'node 1', 'node 1.0', 'node 1.0.1']
