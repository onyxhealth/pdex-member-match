import os

from flask import Flask, request, jsonify, Response
from icecream import ic
from .settings import DEFAULT_PORT
from .settings import DEFAULT_DESCRIPTION, DEFAULT_SEVERITY, DEFAULT_CODE, DEFAULT_STATUS_CODE, REQUIRED_PARAMETERS
from .classes import OperationOutcomeException
from .datavalidation import unique_match_on_coverage, load_parameters, evaluate_consent, get_metadata, call_fhir, write_fhir
import logging

import json
import uuid

debug_mode = True
app = Flask(__name__)


def validated_data(data={}):
    '''
    check for data validity
    :return:
    '''

    validated = True
    error = {'status_code': DEFAULT_STATUS_CODE,
             'code': DEFAULT_CODE,
             'severity': DEFAULT_SEVERITY,
             'description': DEFAULT_DESCRIPTION}

    if (data.get('resourceType') and data.get('id')):
        if not (data['resourceType'] == "Parameters" and data['id'] == 'member-match-in'):
            validated = False
            error['description'] = "member-match-in parameters not submitted in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    else:
        validated = False
        error['description'] = "badly formatted parameters in POST body"
        error['status_code'] = 422
        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])

    if data.get('parameter'):
        ic(f"Number of Parameters:{len(data['parameter'])}")
        if len(data['parameter']) > 2:
            pass
        else:
            validated = False
            error['description'] = "insufficient parameters in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])
        required_parameters = []
        for i in data['parameter']:
            if i.get('name'):
                if i['name'] in REQUIRED_PARAMETERS:
                    required_parameters.append(i['name'])
        ic(len(required_parameters))
        ic(required_parameters)
        ic(len(REQUIRED_PARAMETERS))
        if (len(required_parameters) != len(REQUIRED_PARAMETERS)):
            validated = False
            error['description'] = "Required parameters are missing check for " + ', '.join(map(str, REQUIRED_PARAMETERS))
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    else:
        validated = False
        error['description'] = "no parameter element in POST body"
        error['status_code'] = 422
        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])
    ic(f"data is good")
    return data


def build_operation_outcome(error, ooid=uuid.uuid4()):
    '''
    Create an Operation Outcome dict
    :param error:
    :param id:
    :return:
    '''
    ic(f"Executing OO Build:{error}")
    oo = {
  "resourceType" : "OperationOutcome",
  "id" : str(ooid),
  "text" : {
    "status" : "generated",
    "div" : "<div xmlns=\"http://www.w3.org/1999/xhtml\">\n      <p>" + error['description'] + "</p>\n    </div>"
  },
  "issue" : [{
    "severity" : error['severity'],
    "code" : error['code'] + ":" + str(error['status_code']),
    "details" : {
      "text" : error['description']
    }
  }]
}
    return oo


@app.errorhandler(OperationOutcomeException)
def handle_operation_outcomes_exception(error):
    ic(f"error:{type(error)}")
    response = Response(json.dumps(build_operation_outcome(vars(error)), indent=4),
                        status=error.status_code,
                        mimetype='application/json')
    ic(response)
    return response


@app.errorhandler(OperationOutcomeException)
def handle_operation_outcomes_exception(error):
    ic(f"error:{type(error)}")
    response = Response(json.dumps(build_operation_outcome(vars(error)), indent=4),
                        status=error.status_code,
                        mimetype='application/json')
    ic(response)
    return response


@app.route('/')
def hello_world():
    '''
    Test the matcher works
    '''
    return 'Hello, World!'


@app.route('/metadata')
def metadata():
    '''
    Test the HAPI Server access
    :return:
    '''

    status_code, response = get_metadata()
    ic(status_code)
    ic(response)
    # return "hello! I'm HAPI"
    return jsonify(response)


@app.route('/Patient/$member-match', methods=['POST'])
def member_match():
    '''
    process a member-match operation
    :return:
    '''

    data = request.get_json()

    v_data = validated_data(data)
    # if v_data:
    #     result = True
    # else:
    #     result = False
    member, coverage, consent = load_parameters(data)
    m_data = unique_match_on_coverage(coverage, member)
    ic(m_data)
    # ic(m_data[0])
    ic(m_data[1])
    ic('entry' in m_data[1])
    m_data1 = m_data[1]
    member_id = ""
    if 'entry' in m_data1:
        ic(m_data1['entry'])
        ic(len(m_data1['entry']))
        if len(m_data1['entry']) > 0:
            ic("second if statement ran")
            member_id = m_data1['entry'][0]['resource']['beneficiary']['reference']
            ic(member_id)
            # We have a unique member. Now check Consent
            comply = evaluate_consent(consent, member_id)
            if comply:
                return jsonify(
                    {
                        'resourceType': 'Parameters',
                        #'id': member_id,
                        "parameter" : [
                            {
                                "name" : "MemberIdentifier",
                                "valueIdentifier" : {
                                    "type" : {
                                        "coding" : [
                                            {
                                                "system" : "http://terminology.hl7.org/CodeSystem/v2-0203",
                                                "code" : "MB"
                                            }
                                        ]
                                    },
                                    "system" : "http://example.org/target-payer/identifiers/member",
                                    "value" : "55678",
                                    "assigner" : {
                                    "display" : "Old Payer"
                                    },
                                    'id': member_id
                                }
                            }
                    ],
                    }
                )
            else:
                error = {'status_code': 422,
                     'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                     'description': "Unable to comply with consent"}

                raise OperationOutcomeException(status_code=error['status_code'],
                                                description=error['description'])

    error = {'status_code': 422,
            'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
            'description': "Unable to match Patient"}

    raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    return()

@app.route('/resource/<string:resourceType>', methods=['GET', 'POST'])
def get_resource(resourceType):
    '''
    process getting resource data info
    :return:
    '''
    logging.info("resource/<resourceType> hit")
    if request.method == 'POST':
        data = request.get_json()
        status_code, response = write_fhir("POST", data)
        print(status_code, response)
        return jsonify(response)
    else:
        status_code, response = call_fhir("GET", resourceType)
        print(status_code, response)
        return jsonify(response)



if __name__ == '__main__':

    app.run(port=DEFAULT_PORT, debug=debug_mode)

