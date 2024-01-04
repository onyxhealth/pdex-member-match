# Da Vinci Payer Data Exchange (PDex) Single Member-Match Operation

The purpose of this operation is to receive a parameter bundle, following the definition in the Da Vinci 
Health Record Exchange (HRex) IG.

The content of the bundle are used to perform a single member-match. if a 
successful match is made the operation returns a FHIR Patient ID.

The order of processing logic is as follows:

1. Match using Coverage resource.
2. Match using Coverage resource and patient Demographics.

A match can fail for the following reasons:

- No match found
- Too many matches

An operation Outcome should be returned with an Unproccessable Entity status code (422).

## Consent Handling

If a match is made it is then necessary to check the Consent resource. The 
Consent resource hastwo options for data sensitivity.

- Share all data
- Share non-sensitive data

Whether data can be shared with the requesting Payer will
depend upon how and what data is available in the FHIR API. There are 
three scenarios:

- No sensitive data is available via the FHIR API
- Sensitive data is available in the FHIR API and is labelled as sensitive
- Sensitive data is available in the FHIR API but is NOT labelled.

The Single Member Match function will have a setting to identify which category the FHIR Store supports:
# Values = "EXCLUDED" | "INCLUDED_LABELLED" | "INCLUDED_NOLABEL"
FHIR_STORE_SENSITIVITY = "EXCLUDED"  

In the first two scenarios the Payer can comply with the Censent and release data.
In the last scenario the Payer will have to decline to share data
if the member requested that only non-sensitive data be shared.

If Consent can't be complied with an unprocessable entity (422) status code
is returned with an operation outcome message.

## Consent values

- Allow non-sensitive:

         "policy": [
          {
            "uri": "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#regular"
          }
        ],

- Allow Sensitive and Non-Sensitive:

         "policy": [
          {
            "uri": "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#sensitive"
          }
        ],


## Test Environment

- Create a server (using HAPI)
- load sample coverage and patient resources
- create new parameter bundles that will enable matches to Patient and Coverage resources
- create new parameter bundles and patient and coverage resources that will fail

# PDex Multi-Member Match Operation

The Parameter bundle received by the Multi-Member Match Operation has a series of member bundles to perform 
a member match against. The same matching logic is applied as is used for a single member-match.

The differences in processing a multi-member match is as follows:

- Operation Outcomes should not halt processing.
- The results of the member-match will be added to a group resource.
- There are three possible member-match outcomes: Match, NoMatch and Match but Consent Constraint applies.
- Members matches will be assigned to a group for the relevant outcome (Match, NoMatch, ConsentConstraint).
- In the case of a match the Matched Patient.id is returned in group.member.entity.
- The submitted patient record is added as a contained resource referenced from the extension in group.member.entity.
- For NoMatch and ConsentConstraint the submitted patient record is added to group.member.extension
- The submitted patient records are always added as a contained resource since they will not have been added to the FHIR Store.
- Contained resources are added to group.contained.
- 

