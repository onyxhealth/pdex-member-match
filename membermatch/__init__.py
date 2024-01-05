import os

from flask import Flask, request, jsonify, Response
from icecream import ic
from .settings import DEFAULT_PORT
from .settings import DEFAULT_DESCRIPTION, DEFAULT_SEVERITY, DEFAULT_CODE, \
    DEFAULT_STATUS_CODE, REQUIRED_PARAMETERS
from .classes import OperationOutcomeException
from .datavalidation import unique_match_on_coverage, load_parameters, \
    evaluate_consent, get_metadata, create_member_match_response, write_group, populate_return_parameter

import json
import uuid

debug_mode = True
app = Flask(__name__)
ic(f"in __init__.py")

def wrong_match(bundle_type="", operation_type=""):
    """
    Create an error outcome
    :param bundle_type:
    :param operation_type:
    :return:
    """
    # We got an unexpected  bundle type
    error = setup_error_dict()
    error['description'] = f"incorrect submission [{bundle_type}]to {operation_type} operation"
    error['status_code'] = 422
    raise OperationOutcomeException(status_code=error['status_code'],
                                    description=error['description'])
    return


def setup_error_dict():
    """
    Setup the default error dict
    :param:
    :return error:
    """
    error = {'status_code': DEFAULT_STATUS_CODE,
             'code': DEFAULT_CODE,
             'severity': DEFAULT_SEVERITY,
             'description': DEFAULT_DESCRIPTION}
    return error


def validate_parameter_type(data={}):
    """
    Check for Parameter bundle type.
    member-match-in = single member match
    payer-multi-member-match-in = multi-member-match
    :param data:
    :return: "single" | "multi"
    """
    validated = True
    operation_type = "undefined"
    error = setup_error_dict()
    print(f"validating parameter type")
    print(f"{type(data)}")
    json_data = json.loads(data)
    # print(f"data:[{data}]")
    print(json_data['resourceType'])
    if not (json_data['resourceType'] and json_data['id']):
        print(f"problem with resourceType[{json_data['resourceType']}] and id[{json_data['id']}]")
        # Missing resourceType and id in data
        validated = False
        error['description'] = "badly formatted parameters in POST body"
        error['status_code'] = 422
        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])
    else:
        print(f"evaluating resourceType {json_data['resourceType']} ")
        # we have resourceType and id key values to assess
        if not json_data['resourceType'] == "Parameters":
            validated = False
            error['description'] = "resourceType:Parameters not submitted in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])
        else:
            # we have a Parameters resource
            # Lets see if it is a single member-match or a multi-member-match
            if json_data['id'] == 'member-match-in':
                validated = True
                operation_type = "single"
            elif json_data['id'] == 'payer-multi-member-match-in':
                validated = True
                operation_type = "multi"

    if validated:
        return operation_type


def validated_data(data={}, bundle_type="single"):
    """
    :param data:
    :param bundle_type single | multi :
    check for data validity - i.e. do we have all the parameter elements needed to match a single member
    data will pass in the
    NOTE: data should have been tested with validate_parameter_type to ensure it is a correct bundle
    So in this validation we can simplify to test for the correct content in the bundle.
    For single member-match we will pass in the full data element.
    For Multi-Member Match we will pass in the part element which will have data for a single member.
    Multi-Member Match needs to fail silently and carry on, reporting the failure in the return.
    :return data:
    """

    validated = True
    parm_type = "single"
    error = setup_error_dict()
    if bundle_type.lower() == "multi":
        parm_type = "part"
    else:
        parm_type = "parameter"

    if data.get(parm_type):
        ic(f"Number of Parameters:{len(data[parm_type])}")
        if len(data[parm_type]) > 2:
            pass
        else:
            validated = False
            if bundle_type == "single":
                error['description'] = f"insufficient {parm_type}.parameters in POST body"
                error['status_code'] = 422
                raise OperationOutcomeException(status_code=error['status_code'],
                                                description=error['description'])
        required_parameters = []
        for i in data[parm_type]:
            if i.get('name'):
                if i['name'] in REQUIRED_PARAMETERS:
                    required_parameters.append(i['name'])
        ic(len(required_parameters))
        ic(required_parameters)
        ic(len(REQUIRED_PARAMETERS))
        if (len(required_parameters) != len(REQUIRED_PARAMETERS)):
            validated = False
            if bundle_type == "single":
                error['description'] = "Required parameters are missing check for " + ', '.join(map(str, REQUIRED_PARAMETERS))
                error['status_code'] = 422
                raise OperationOutcomeException(status_code=error['status_code'],
                                                description=error['description'])

    else:
        validated = False
        if bundle_type == "single":
            error['description'] = f"no {parm_type} element in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])
    if validated:
        ic(f"data is good")
    else:
        ic(f"data had a problem")
    return {"data": data, "validated": validated}


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

#
# @app.errorhandler(OperationOutcomeException)
# def handle_operation_outcomes_exception(error):
#     ic(f"error:{type(error)}")
#     response = Response(json.dumps(build_operation_outcome(vars(error)), indent=4),
#                         status=error.status_code,
#                         mimetype='application/json')
#     ic(response)
#     return response


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

    status_code, response = get_metadata(calltype='GET')
    ic(status_code)
    ic(response)
    # return "hello! I'm HAPI"
    return jsonify(response)


@app.route('/$member-match', methods=['POST'])
def single_member_match():
    """
    process a single member-match operation
    :return:
    """

    data = request.get_json()

    bundle_type = validate_parameter_type(data)
    if not bundle_type.lower() == "single":
        throw_error = wrong_match(bundle_type=bundle_type, operation_type="/$member-match")
        # We got an unexpected  bundle type
    # We should have a bundle_type of "single"
    v_data = validated_data(data, bundle_type=bundle_type)
    validated =v_data['validated']

    member, coverage, consent = load_parameters(data, bundle_type=bundle_type)
    m_data = unique_match_on_coverage(coverage, member)
    ic(m_data)
    ic(m_data[0])
    ic(m_data[1])
    m_data1 = m_data[1]
    member_id = ""
    if 'entry' in m_data1:
        if len(m_data1['entry']) == 1:
            member_id = m_data1['entry'][0]['resource']['beneficiary']['reference']
            ic(member_id)
            # We have a unique member. Now check Consent
            comply = evaluate_consent(consent, member_id, bundle_type=bundle_type)
            if (comply and len(member_id) > 0):
                return jsonify({'member_id': member_id})
            else:
                error = {'status_code': 422,
                         'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                         'description': f"Unable to comply with consent for member:{member_id}"}

                raise OperationOutcomeException(status_code=error['status_code'],
                                                description=error['description'])

    error = {'status_code': 422,
             'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
             'description': "Unable to match Patient"}

    raise OperationOutcomeException(status_code=error['status_code'],
                                    description=error['description'])

    return()


@app.route('/$bulk-member-match', methods=['POST'])
def multi_member_match():
    """
    process a multi member-match operation
    :return:
    """
    print("entering multi-member-match")

    data = request.get_json()
    print(f"{type(data)}")
    print(f"We have the data: {data[:40]}")
    print(f"testing bundle_type")
    bundle_type = validate_parameter_type(data)
    print(f"bundle_type:{bundle_type}")
    if not bundle_type.lower() == "multi":
        throw_error = wrong_match(bundle_type=bundle_type, operation_type="/$bulk-member-match")
        # We got an unexpected  bundle type

    # We should have a bundle_type of "multi"
    json_data = json.loads(data)

    print(json_data['parameter'])
    print(f"processing each bundle. {len(json_data['parameter'])}")
    # group_response = {}
    matched = []
    nomatch = []
    noconsent = []
    ic(len(json_data['parameter']))
    for part in json_data['parameter']:
        # get each bundle of parameters
        print(f"getting validated_data")
        v_data = validated_data(part, bundle_type=bundle_type)
        # print(f"loading up member,coverage and consent from parameters")
        member, coverage, consent = load_parameters(part, bundle_type=bundle_type)
        print(f"got member, coverage and consent- now try a match")
        m_data = unique_match_on_coverage(coverage, member)
        print(f"back from a unique match")
        # ic(m_data)
        # ic(m_data[0])
        if 'total' in m_data[1]:
            ic(m_data[1]['total'])
        else:
            ic(m_data[1])
        m_data1 = m_data[1]
        ic(m_data1)
        member_id = ""
        if 'entry' in m_data1:
            if len(m_data1['entry']) == 1:
                member_id = m_data1['entry'][0]['resource']['beneficiary']['reference']
                ic(member_id)
                # We have a unique member. Now check Consent
                comply = evaluate_consent(consent, member_id, bundle_type=bundle_type)
                if  (comply and len(member_id) > 0):
                    # we need to create Group
                    # add found member info to group
                    print(f"Added {member_id} to Matched")
                    matched.append({"member": member_id, "member_input": member})
                    # return jsonify({'member_id': member_id})
                else:
                    # add failed member info to group
                    print(f"Adding {member_id} to NoConsent")
                    noconsent.append(member)
            else:
                # we didn't get a unique match.
                print(f"Adding Member to NoMatch - not unique")
                nomatch.append(member)
        else:
            # we got nothing back
            print(f"no match for Member {member['name']}:[{member_id}]")
            nomatch.append(member)
    ic(len(matched), len(nomatch), len(noconsent))
    # end for
    # now we write the Group resource to the FHIR Store
    # if written successfully we need to return the Group resource in the Parameter Response
    # group_resource = write_group(group_response)
    # parameter_response = populate_return_parameter(group_resource)
    # return jsonify(parameter_response)
    # print(f"Return a basic message")
    parameter_response = {"data-matched": matched, "data-nomatch": nomatch, "data-noconsent": noconsent}
    return jsonify({"message": "you reached the $bulk-member-match-operation", "data": parameter_response})


if __name__ == '__main__':
    ic(f"Entering main __init__.py module")
    ic(f"{DEFAULT_PORT}")
    app.run(port=DEFAULT_PORT, debug=debug_mode)

