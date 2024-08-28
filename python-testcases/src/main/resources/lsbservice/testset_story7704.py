"""
@copyright: Ericsson Ltd
@since:     January 2015
@author:    etomgly
@summary:   Tests for Service plugin stories:
            LITPCDS-7704
"""
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import test_constants
from xml_utils import XMLUtils


class Story7704(GenericTest):
    """
    LITPCDS-7704:
        The Service plugin is used to ensure a service is running on
        a node
    """

    def setUp(self):
        """Run before every test"""
        super(Story7704, self).setUp()
        self.redhat = RHCmdUtils()
        self.ms_node = self.get_management_node_filename()
        self.mn_nodes = self.get_managed_node_filenames()
        self.xml = XMLUtils()

    def tearDown(self):
        """Run after every test"""
        super(Story7704, self).tearDown()

    def export_validate_xml(self, path, file_name):
        """
        Description
            Exports the created item to xml file and Validates the xml file
        Actions:
            1: run export command on item path
            2: validate the xml file
        """
        # EXPORT CREATED PROFILE ITEM
        self.execute_cli_export_cmd(self.ms_node, path, file_name)
        # validate xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, stderr, exit_code = self.run_command(self.ms_node, cmd)
        self.assertNotEqual([], stdout)
        self.assertEqual(0, exit_code)
        self.assertEqual([], stderr)

    def load_xml(self, path, file_name):
        """
        Description
            Loads the created xml file and Validates the xml file
        Actions:
            1. Loads the xml
            2. Expects an error
        """
        # this is done in each test to test the item with xml it an
        # already exists error is expected
        _, stderr, _ = self.execute_cli_load_cmd(
            self.ms_node, path, file_name, expect_positive=False)
        self.assertTrue(self.is_text_in_list("ItemExistsError ", stderr))

    def is_service_not_running(self, service, node):
        """
        Description:
            Checks if a service is not running on a node
        """
        cmd = self.redhat.get_systemctl_status_cmd(service)
        _, err, ret_code = self.run_command(node, cmd)
        # expect an error
        self.assertTrue(self.is_text_in_list(
            'Unit {0}.service could not be found.'.format(service), err))
        # expect the return code to equal 4
        self.assertEqual(4, ret_code, "Failed to return 4")

    @attr('all', 'revert', 'story7704', 'story7704_tc01', 'cdb_priority1')
    def test_01_p_ensure_service_on_ms(self):
        """
        @tms_id: litpcds_7704_tc01
        @tms_requirements_id: LITPCDS-7704
        @tms_title: Add service to MS
        @tms_description: Test that ensures we can create a service on the ms
        @tms_test_steps:
            @step: create service
            @result: Service is created in litp model
            @step: create a package
            @result: Package is created in litp model
            @step: inherit package to ms
            @result: Package is inherited onto node
            @step: Create and run the plan
            @result: Plan is created and runs successfully
            @step: Ensure service is running
            @result: Service is running
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "vsftpd"
        app_path = "/vsftpd_test01"

        service_url = "/ms/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + app

        ms_items = "/ms/items"
        ms_items_url = ms_items + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit package to ms
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_items_url, package)

        # 4. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 5. Ensure service is running
        self.get_service_status(self.ms_node, app,
                                assert_running=True,
                                su_root=False)

    @attr('all', 'revert', 'story7704', 'story7704_tc02')
    def test_02_p_ensure_service_on_one_node(self):
        """
        @tms_id: litpcds_7704_tc02
        @tms_requirements_id: LITPCDS-7704
        @tms_title: Add service to MN
        @tms_description: Test that ensures we can create a service on a MN
        @tms_test_steps:
            @step: Create service
            @result: Service is created in litp model
            @step: create a package
            @result: Package is created in litp model
            @step: inherit service to node1
            @result: Service is inherited onto node
            @step: inherit package
            @result: Package is inherited onto node
            @step: Create and run the plan
            @result: Plan is created and runs successfully
            @step: Ensure service is running
            @result: Service is running
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "vsftpd"
        app_path = "/vsftpd_test02"

        service_url = "/software/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + app

        software_services = "/software/services" + app_path + \
                            "/packages" + app_path

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node1_url = nodes_url[0] + '/services' + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit service to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url, service)

        # 4. inherit package
        self.execute_cli_inherit_cmd(
            self.ms_node, software_services, package)

        # 5. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 6. Ensure service is running
        self.get_service_status(self.mn_nodes[0], app,
                                assert_running=True,
                                su_root=False)

    @attr('all', 'revert', 'story7704', 'story7704_tc03')
    def test_03_p_ensure_service_on_two_nodes(self):
        """
        @tms_id: litpcds_7704_tc03
        @tms_requirements_id: LITPCDS-7704
        @tms_title: Add service to 2 MN's
        @tms_description: Test that ensures we can create a service on 2 MN's
        @tms_test_steps:
            @step: Create service
            @result: Service is created in litp model
            @step: create a package
            @result: Package is created in litp model
            @step: inherit service to node1
            @result: Service is inherited onto node
            @step: inherit package
            @result: Package is inherited onto node
            @step: inherit service to node2
            @result: Package is inherited onto node
            @step: Create and run the plan
            @result: Plan is created and runs successfully
            @step: Ensure service is running on node1
            @result: Service is running
            @step: Ensure service is running on node2
            @result: Service is running
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "vsftpd"
        app_path = "/vsftpd_test03"

        service_url = "/software/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + app

        software_services = "/software/services" + app_path + \
                            "/packages" + app_path

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node1_url = nodes_url[0] + '/services' + app_path
        node1_url2 = nodes_url[1] + '/services' + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit service to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url, service)

        # 4. inherit package
        self.execute_cli_inherit_cmd(
            self.ms_node, software_services, package)

        # 5. inherit service to node2
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url2, service)

        # 6. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 7. Ensure service is running on node1
        self.get_service_status(self.mn_nodes[0], app,
                                assert_running=True,
                                su_root=False)

        # 8. Ensure service is running on node2
        self.get_service_status(self.mn_nodes[1], app,
                                assert_running=True,
                                su_root=False)

    @attr('all', 'revert', 'story7704', 'story7704_tc04')
    def test_04_p_ensure_service_removed(self):
        """
        @tms_id: litpcds_7704_tc04
        @tms_requirements_id: LITPCDS-7704
        @tms_title: Remove service from MS
        @tms_description: Test that ensures we can remove a service on the ms
        @tms_test_steps:
            @step: create service
            @result: Service is created in litp model
            @step: create a package
            @result: Package is created in litp model
            @step: inherit package to ms
            @result: Package is inherited onto node
            @step: Create and run the plan
            @result: Plan is created and runs successfully
            @step: Ensure service is running
            @result: Service is running
            @step: Remove the service
            @result: Item is in ForRemoval state
            @step: Create and run plan
            @result: Plan is created and runs successfully
            @step: Ensure service is not running
            @result: service is not running
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "vsftpd"
        app_path = "/vsftpd_test04"

        service_url = "/ms/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + app

        ms_items = "/ms/items"
        ms_items_url = ms_items + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit package to ms
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_items_url, package)

        # 4. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 5. Ensure service is running
        self.get_service_status(self.ms_node, app,
                                assert_running=True,
                                su_root=False)

        # 6. Remove the service
        self.execute_cli_remove_cmd(self.ms_node, service)
        self.execute_cli_remove_cmd(self.ms_node, ms_items_url)

        # 7. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 8. Ensure service is not running
        self.is_service_not_running(app, self.ms_node)

    @attr('all', 'revert', 'story7704', 'story7704_tc05')
    def test_05_n_create_duplicate_service(self):
        """
        @tms_id: litpcds_7704_tc05
        @tms_requirements_id: LITPCDS-7704
        @tms_title: cannot create duplicate services
        @tms_description: Test that ensures we cannot create duplicate services
        @tms_test_steps:
            @step: create a service for service xxxx
            @result: Service is created in litp model
            @step: create a service for service xxxx
            @result: Service is created in litp model
            @step: try to create plan
            @result: create_plan command is run
            @step: ensure plan creation fails
            @result: Plan fails with expected error message
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "vsftpd"
        app_path = "/vsftpd_test05"
        app_path2 = "/vsftpd_test05_b"

        service_url = "/software/services"
        service = service_url + app_path
        service2 = service_url + app_path2
        service_props = "service_name=" + "'" + app + "'"

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node1_url = nodes_url[0] + '/services' + app_path
        node1_url2 = nodes_url[0] + '/services' + app_path2

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)

        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. Create service
        self.execute_cli_create_cmd(self.ms_node, service2,
                                    "service", service_props)

        # xml test
        self.export_validate_xml(service2, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 3. inherit service to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url, service)

        # 4. inherit service2 to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url2, service2)

        # 5. try to create plan
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)

        # 6. ensure plan creation fails
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Create plan failed: Duplicate service '
                        '"vsftpd" defined')

    @attr('all', 'revert', 'story7704', 'story7704_tc06')
    def test_06_n_create_disallowed_services(self):
        """
        @tms_id: litpcds_7704_tc06
        @tms_requirements_id: LITPCDS-7704
        @tms_title: cannot create a disallowed service
        @tms_description: Test to ensures we cannot create a disallowed service
        @tms_test_steps:
            @step: create a service for a disallowed service_name
            @result: ensure item creation fails with correct error
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "mcollective"
        app_path = "/mcollective_test06"

        service_url = "/ms/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        # 1. create a service for a disallowed service
        _, stderr, _ = _, stderr, _ = self.execute_cli_create_cmd(
            self.ms_node, service, "service", service_props,
            expect_positive=False)

        # 2. ensure iten creation fails with correct error
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Service "mcollective" is managed by LITP')

    @attr('all', 'revert', 'story7704', 'story7704_tc07')
    def test_07_n_create_disallowed_services_on_peer_node(self):
        """
        @tms_id: litpcds_7704_tc07
        @tms_requirements_id: LITPCDS-7704
        @tms_title: cannot create a disallowed service on MN
        @tms_description: Test that ensures we cannot create a disallowed
                 service on a peer node
        @tms_test_steps:
            @step: create a service for service xxxx
            @result: Service is created in litp model
            @step: create a package
            @result: Package is created in litp model
            @step: inherit service to node1
            @result: service is inherited onto node
            @step: inherit package
            @result: Package is inherited onto node
            @step: try to create plan
            @result: create_plan command is run
            @step: ensure plan creation fails
            @result: Plan fails with expected error message
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "sshd"
        app_path = "/sshd_test07"

        service_url = "/software/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + app

        software_services = "/software/services" + app_path + \
                            "/packages" + app_path

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node1_url = nodes_url[0] + '/services' + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit service to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url, service)

        # 4. inherit package
        self.execute_cli_inherit_cmd(
            self.ms_node, software_services, package)

        # 5. try to create plan
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)

        # 6. ensure plan creation fails
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Create plan failed: Service "sshd" is '
                        'managed by LITP')

    @attr('all', 'revert', 'story7704', 'story7704_tc08')
    def test_08_n_disallowed_service_on_ms_allowed_on_node(self):
        """
        @tms_id: litpcds_7704_tc08
        @tms_requirements_id: LITPCDS-7704
        @tms_title: Disallowed service on ms allowed on node
        @tms_description: Test that ensures we cannot create a disallowed
                 service on a ms but can on a peer node
        @tms_test_steps:
            @step: Create a service for service xxxx
            @result: Service is created in litp model
            @step: Create a package
            @result: Package is created in litp model
            @step: Inherit service to node1
            @result: Package is inherited onto node
            @step: Try to create plan
            @result: Create_plan command is run
            @step: Ensure plan creation fails
            @result: Plan creation fails with expected error message
            @step: Remove the service
            @result: Item is in ForRemoval state
            @step: Create service
            @result: Service is created in litp model
            @step: Create a package
            @result: Package is created in litp model
            @step: Inherit service to node1
            @result: Service is inherited onto node
            @step:. Inherit package
            @result: Package is inherited onto node
            @step:. Create and run the plan
            @result: Plan is created and runs successfully
            @step:. Ensure service is running
            @result: Service is running
        @tms_test_precondition:NA
        @tms_execution_type: Automated
        """
        app = "rabbitmq-server"
        app_path = "/rabbitmq-server_test08"
        app_path2 = "/rabbitmq-server_test08_b"
        package_name = "EXTRlitprabbitmqserver_CXP9031043.noarch"

        service_url = "/ms/services"
        service = service_url + app_path
        service_props = "service_name=" + "'" + app + "'"

        package_url = "/software/items"
        package = package_url + app_path
        package_props = "name=" + package_name

        ms_items = "/ms/items"
        ms_items_url = ms_items + app_path

        # 1. Create service
        self.execute_cli_create_cmd(self.ms_node, service,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service, "xml_story7704.xml")
        self.load_xml(service_url, "xml_story7704.xml")

        # 2. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package, "package", package_props)

        # xml test
        self.export_validate_xml(package, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 3. inherit package to ms
        self.execute_cli_inherit_cmd(
            self.ms_node, ms_items_url, package)

        # 4. try to create plan
        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)

        # 5. ensure plan creation fails
        self.assertTrue(self.is_text_in_list('ValidationError', stderr),
                        'Create plan failed: Service "rabbitmq-server" '
                        'is managed by LITP')

        # 6. Remove the service
        self.execute_cli_remove_cmd(self.ms_node, ms_items_url)
        self.execute_cli_remove_cmd(self.ms_node, package)
        self.execute_cli_remove_cmd(self.ms_node, service)

        service_url2 = "/software/services"
        service2 = service_url2 + app_path2
        package2 = package_url + app_path2

        software_services = "/software/services" + app_path2 + \
                            "/packages" + app_path2

        nodes_url = self.find(self.ms_node, "/deployments", "node", True)
        node1_url = nodes_url[0] + '/services' + app_path2

        # 7. Create service
        self.execute_cli_create_cmd(self.ms_node, service2,
                                    "service", service_props)
        # xml test
        self.export_validate_xml(service2, "xml_story7704.xml")
        self.load_xml(service_url2, "xml_story7704.xml")

        # 8. create a package
        self.execute_cli_create_cmd(
            self.ms_node, package2, "package", package_props)

        # xml test
        self.export_validate_xml(package2, "xml_story7704.xml")
        self.load_xml(package_url, "xml_story7704.xml")

        # 9. inherit service to node1
        self.execute_cli_inherit_cmd(
            self.ms_node, node1_url, service2)

        # 10. inherit package
        self.execute_cli_inherit_cmd(
            self.ms_node, software_services, package2)

        # 11. Create and run the plan
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(
            self.ms_node, test_constants.PLAN_COMPLETE))

        # 12. Ensure service is running
        self.get_service_status(self.mn_nodes[0], app,
                                assert_running=True,
                                su_root=True)
