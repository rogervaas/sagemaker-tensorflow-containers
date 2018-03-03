import os

from sagemaker import fw_utils

from test.integ.utils import copy_resource, create_config_files, file_exists
from test.integ.conftest import SCRIPT_PATH
from test.integ.docker_utils import HostingContainer, train


def test_wide_deep(docker_image, sagemaker_session, opt_ml):
    resource_path = os.path.join(SCRIPT_PATH, '../resources/wide_deep')

    copy_resource(resource_path, opt_ml, 'code')
    copy_resource(resource_path, opt_ml, 'data', 'input/data')

    s3_source_archive = fw_utils.tar_and_upload_dir(session=sagemaker_session.boto_session,
                                                    bucket=sagemaker_session.default_bucket(),
                                                    s3_key_prefix='test_job',
                                                    script='wide_deep.py',
                                                    directory=os.path.join(resource_path, 'code'))

    create_config_files('wide_deep.py', s3_source_archive.s3_prefix, opt_ml,
                          dict(training_steps=1, evaluation_steps=1))

    os.makedirs(os.path.join(opt_ml, 'model'))

    train(docker_image, opt_ml)

    assert file_exists(opt_ml, 'model/export/Servo'), 'model was not exported'
    assert file_exists(opt_ml, 'model/checkpoint'), 'checkpoint was not created'
    assert file_exists(opt_ml, 'output/success'), 'Success file was not created'
    assert not file_exists(opt_ml, 'output/failure'), 'Failure happened'

    with HostingContainer(image=docker_image, opt_ml=opt_ml, script_name='wide_deep.py') as c:
        c.execute_pytest('test/integ/container_tests/wide_deep_prediction.py')
