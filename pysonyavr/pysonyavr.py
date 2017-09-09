#!/usr/bin/python
# coding: utf-8

'''
Sony AVR class
'''

import logging
import random
import re


# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


class SonyAvr(object):
    '''
    Sony AVR class. Suitable for Sony SRS devices.
    Tested on a pair of Sony SRS-ZR7.
    '''
    def __init__(self, host, port=54480):
        self.host = host
        self.port = port

    def __api_call(self, endpoint, method, api_version=1.0, params=None):
        import requests
        url = 'http://{}:{}/sony/{}'.format(self.host, self.port, endpoint)

        # Construct request parameters
        request_id = random.randint(0, 50000)
        json_params = {
            'id': request_id,
            'method': method,
            'params': params if params is not None else [],
            'version': str(api_version)
        }
        _LOGGER.debug('JSON Parameters: %s', json_params)

        # API call
        res = requests.post(url, json=json_params)
        _LOGGER.debug('Raw response: %s', res.text)
        jres = res.json()

        # Error handling
        if not res.ok or 'error' in jres:
            _LOGGER.error(jres)
        if jres.get('id') != request_id:
            _LOGGER.warning('The request id in the response differs')
        res.raise_for_status()

        # Normally the results reside under the "result" key, except for
        # get_method_type() where the are available at "results"
        return jres.get('result') if 'result' in jres else jres.get('results')

    @property
    def _supported_apis(self):
        '''
        Get the JSON list of supported API calls
        '''
        return self.__api_call(
            endpoint='guide',
            method='getSupportedApiInfo',
            params=[{}],  # required
            api_version=1.0)[0]

    @property
    def _supported_methods(self):
        '''
        Get a list of supported methods
        '''
        methods = []
        for api in self._supported_apis:
            service = api.get('service')
            for method in api.get('apis'):
                methods.append('{}.{}'.format(service, method.get('name')))
        return methods

    @property
    def _services(self):
        '''
        Get the list of available services (ie. API types)
        '''
        return [x.get('service') for x in self._supported_apis]

    @property
    def power_status(self):
        '''
        Current power status
        '''
        res = self.__api_call(
            endpoint='system',
            method='getPowerStatus',
            api_version=1.1)
        return res[0].get('status')

    @property
    def is_on(self):
        '''
        Whether this device is currently on
        '''
        return self.power_status == 'active'

    @property
    def state(self):
        '''
        Current state of the device (playing, stopped...)
        '''
        device_state = self.get_current_media_info()
        return device_state.get('stateInfo', {}).get('state')

    @property
    def current_input(self):
        '''
        Currently active input
        '''
        uri = self.get_current_media_info().get('source')
        title = self._get_input_title(uri)
        if not title:
            _LOGGER.warning('Unable to find source title for source %s', uri)
            return uri
        return title

    @property
    def schemes(self):
        '''
        List of available schemes
        '''
        res = self.__api_call(
            endpoint='avContent',
            method='getSchemeList',
            api_version=1.0
        )[0]
        return [x.get('scheme') for x in res]

    @property
    def inputs(self):
        '''
        List of available inputs/sources
        '''
        return sorted([x.get('title') for x in self.get_all_inputs()])

    @property
    def volume(self):
        '''
        Current volume level
        '''
        return self.get_volume_info().get('volume')

    @property
    def volume_percent(self):
        '''
        Current volume level (in %)
        '''
        return float(self.volume / self.max_volume)

    @property
    def min_volume(self):
        '''
        Minimum volume level
        '''
        return self.get_volume_info().get('minVolume')

    @property
    def max_volume(self):
        '''
        Maximum volume level
        '''
        return self.get_volume_info().get('maxVolume')

    @property
    def volume_step(self):
        '''
        Volume stepping
        '''
        return self.get_volume_info().get('step')

    @property
    def is_muted(self):
        '''
        Whether the speaker is currently muted
        '''
        return self.get_volume_info().get('mute') == 'on'

    def _get_method_types(self, endpoint, method=None):
        '''
        Get the help text for an API call
        '''
        match = re.match(r'(.+)\.(.+)', endpoint)
        if match:
            endpoint = match.group(1)
            method = match.group(2)
        res = self.__api_call(
            endpoint=endpoint,
            method='getMethodTypes',
            params=[""],  # required
            api_version=1.0)
        for helpstr in res:
            if helpstr[0] == method:
                return helpstr[1]
        return res

    def _set_power_status(self, status):
        '''
        Set the power status of the device ie. turn on or off
        '''
        return self.__api_call(
            endpoint='system',
            api_version=1.1,
            method='setPowerStatus',
            params=[{'status': status}]
        )

    def turn_on(self):
        '''
        Turn the device on
        '''
        return self._set_power_status('active')

    def turn_off(self):
        '''
        Turn the device off
        '''
        return self._set_power_status('off')

    def get_current_media_info(self):
        '''
        Get the current state of the device
        '''
        return self.__api_call(
            endpoint='avContent',
            method='getPlayingContentInfo',
            params=[{'output': ''}],
            api_version=1.2
        )[0][0]

    def get_volume_info(self):
        '''
        Get the current volume levels, stepping and mute state
        '''
        res = self.__api_call(
            endpoint='audio',
            api_version=1.1,
            method='getVolumeInformation',
            params=[{'output': ''}]
        )
        return res[0][0]

    def set_volume(self, level):
        '''
        Set the volume level
        '''
        if isinstance(level, float):
            assert (level >= 0.0 and level < 1.0), 'Volume must be [0..1]'
            level = int(self.max_volume * level)

        return self.__api_call(
            endpoint='audio',
            api_version=1.1,
            method='setAudioVolume',
            params=[{'output': '', 'volume': str(level)}]
        )

    def raise_volume(self, times=1):
        '''
        Raise the current volume level
        '''
        return self.set_volume(self.volume + (times * self.volume_step))

    def lower_volume(self, times=1):
        '''
        Lower the current volume level
        '''
        return self.set_volume(self.volume - (times * self.volume_step))

    def mute(self, mute=True):
        '''
        Mute the speaker
        '''
        return self.__api_call(
            endpoint='audio',
            api_version=1.1,
            method='setAudioMute',
            params=[{'output': '', 'mute': 'on' if mute else 'off'}]
        )

    def unmute(self):
        '''
        Unmute the speaker
        '''
        return self.mute(mute=False)

    def get_inputs(self, scheme):
        '''
        Return the list of inputs for a given scheme
        '''
        return self.__api_call(
            endpoint='avContent',
            method='getSourceList',
            params=[{'scheme': scheme}],
            api_version=1.2
        )[0]

    def get_all_inputs(self):
        '''
        Get all available inputs
        '''
        sources = []
        for scheme in self.schemes:
            sources += self.get_inputs(scheme)
        return sources

    def set_input(self, source):
        '''
        Set the current input
        '''
        source_uri = self._get_input_uri(source)
        assert source_uri, 'Could not determine source URI'
        return self.__api_call(
            endpoint='avContent',
            api_version=1.2,
            method='setPlayContent',
            params=[{'uri': source_uri}]
        )

    def _get_input_title(self, uri):
        '''
        Convert a source URI to a human-readable name
        '''
        match = re.match(r'(.+)\?port=\d+', uri)
        if match:
            uri = match.group(1)
        for source_info in self.get_all_inputs():
            if uri.lower() == source_info.get('source', '').lower():
                return source_info.get('title')

    def _get_input_uri(self, source):
        '''
        Get the URI of a humand readable input name
        '''
        lsource = source.lower()
        for source_info in self.get_all_inputs():
            if lsource == source_info.get('title', '').lower():
                uri = source_info.get('source')
                # FIXME There may be more than one AUX port
                if lsource == 'audio in':
                    return uri + '?port=1'
                # Fix typos
                match = re.match('exInput:(.*)', uri)
                if match:
                    return 'extInput:{}'.format(match.group(1))
                return uri
